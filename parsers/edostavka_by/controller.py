from parsers.edostavka_by.spider_sync import Spider
from database.session import get_session_factory
from parsers.service import CategoryService
from datetime import datetime as dt


def main():
    spider = Spider()
    session_factory = get_session_factory('catalog')
    service_data = CategoryService(session_factory=session_factory, source_name='edostavka.by')

    """
    Мы имеем класс CatalogCRUD, который требует сессию для создания. Это нормальная практика, 
    так называемый паттерн "Unit of Work". Управление жизненным циклом сессии (создание, коммит, закрытие) должно быть 
    отделено от класса CRUD. Поэтому создаём сессию в менеджере контекста и для каждой сессии создаём объект CatalogCRUD
    """

    for product in spider.crawl():
        """
        Проверяем кеш на наличие артикула (кеш содержит пари ключ - артикул товара, значение ключа - id товара по базе
        данных. Если товар есть в кеше - значит он есть и базе данных. Если нет - делаем новую запись в таблицу товаров и
        связанные таблицы. Затем (вне зависимости от условия выше) делаем запись в таблицу с ценами
        """
        product_id = service_data.articles.get(str(product.productId), None)

        if not product_id:
            # manufacturer
            if product.legalInfo.trademarkName:
                trademark = product.legalInfo.trademarkName
            else:
                trademark = product.legalInfo.title
            manufacturer_id = service_data.get_manufactory_id(trademark=trademark,
                                                              full_name=product.legalInfo.manufacturerName,
                                                              country=product.legalInfo.countryOfManufacture)
            # product
            product_id = service_data.get_product_id(manufacturer_id=manufacturer_id,
                                                     name=product.productName,
                                                     article=str(product.productId),
                                                     description=product.description.productDescription.strip(),
                                                     composition=product.description.composition.strip(),
                                                     storage_info=product.description.storagePeriod.strip(),
                                                     unit=product.quantityInfo.measure,
                                                     barcode=None)

            # categories / product_category
            categories_id_list = []
            for i, category in enumerate(product.categories):
                parent_name = product.categories[i - 1] if i != 0 else None
                category_id = service_data.get_category_id(category_name=category, parent_name=parent_name)
                categories_id_list.append(category_id)
            # relationship product-category
            service_data.save_product_category_relations(product_id=product_id, categories_id=categories_id_list)

            # properties
            for group_property in product.additionalProperties:
                for group_name in group_property.groupProperty:
                    property_id = service_data.get_property_id(group_name.propertyName, group_property.groupName
                                                               if group_property.groupName else None
                                                               )
                    property_values_list = group_name.propertyValue
                    # relationship product-property
                    service_data.save_product_property_values_relations(product_id=product_id,
                                                                        property_id=property_id,
                                                                        values=property_values_list)
            for group_property in product.customPropertyGroup:
                property_id = service_data.get_property_id(group_property.propertyName,
                                                           "Пищевая ценность"
                                                           )
                property_values_list = group_property.propertyValue
                # relationship product-property
                service_data.save_product_property_values_relations(product_id=product_id,
                                                                    property_id=property_id,
                                                                    values=property_values_list)
            # product_images
            service_data.save_product_images_relations(product_id=product_id,
                                                       image_urls_list=product.images)
        # ###  price  ###
        service_data.save_product_price(product_id=product_id,
                                        price=float(product.price.discountedPrice),
                                        date_time=str(dt.now().replace(microsecond=0)))

