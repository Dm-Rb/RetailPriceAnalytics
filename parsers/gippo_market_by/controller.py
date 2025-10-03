from parsers.gippo_market_by.spider_sync import Spider
from database.session import get_session_factory
from parsers.service import CategoryService
from datetime import datetime as dt


def main():
    spider = Spider()
    session_factory = get_session_factory('catalog')
    service_data = CategoryService(session_factory=session_factory, source_name='gippo-market.by')
    for product in spider.crawl():
        product_id = service_data.articles.get(str(product.id), None)
        if not product_id:
            # manufacturer
            manufacturer_id = service_data.get_manufactory_id(trademark=product.manufacturer.trademark,
                                                              full_name=product.manufacturer.name,
                                                              country=product.manufacturer.country)

            # product
            product_id = service_data.get_product_id(manufacturer_id=manufacturer_id,
                                                     name=product.name.strip(),
                                                     article=str(product.id),
                                                     barcode=product.barcode.strip() if product.barcode else None,
                                                     description=product.description.strip() if product.description else None,
                                                     unit=product.unit,
                                                     composition=None,
                                                     storage_info=product.storage_info)
            # categories / product_category
            categories_id_list = []
            for i, category in enumerate(product.categories):
                parent_name = category.parent_title
                try:
                    category_id = service_data.get_category_id(category_name=category.title, parent_name=parent_name)
                except AttributeError:
                    # в некоторых ответах источника содержится некорректные данные родителя категории. для таких случаев
                    # будем использовать предыдущий элемент
                    parent_name = product.categories[i - 1].title if i != 0 else None
                    category_id = service_data.get_category_id(category_name=category.title, parent_name=parent_name)
                categories_id_list.append(category_id)
            # relationship product-category
            service_data.save_product_category_relations(product_id=product_id, categories_id=categories_id_list)

            # properties
            for property in product.properties:
                property_id = service_data.get_property_id(name=property.name,
                                                           group=property.group
                                                           )
                property_values_list = [property.value]
                # relationship product-property
                service_data.save_product_property_values_relations(product_id=product_id,
                                                                    property_id=property_id,
                                                                    values=property_values_list)

            # product_images
            service_data.save_product_images_relations(product_id=product_id,
                                                       image_urls_list=product.images)
        #
        if product.price:
            service_data.save_product_price(product_id=product_id,
                                            price=float(product.price),
                                            date_time=str(dt.now().replace(microsecond=0)))

