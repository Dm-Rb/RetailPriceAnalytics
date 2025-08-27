from spider_sync import Spider
from cache.parsers.edostavkaby.cache import Cache
from database.crud.catalog import CatalogCRUD
from database.session import get_session_factory


def get_cache(session_factory):
    cache = Cache()
    with session_factory() as session:
        catalog_db = CatalogCRUD(session)
        # categories
        [cache.categories.setdefault(item.name, item.id) for item in catalog_db.get_all_categories()]

        # manufacturer
        [cache.manufacturers.setdefault(item.full_name, item.id) for item in catalog_db.get_all_manufacturers()]

        # product_display
        source = 'edostavka.by'
        [cache.product_display.setdefault(item.article, item.product_id) for item in
         catalog_db.get_all_product_display_by_source(source)]

        # properties
        [cache.properties.setdefault(item.name, item.id) for item in catalog_db.get_all_properties()]

    return cache


def save_category_update_cache(session_factory, cache, category_name, parent_name):
    with session_factory() as session:
        catalog_db = CatalogCRUD(session)
        if not parent_name:
            db_id = catalog_db.add_new_category(name=category_name, parent_id=None, parent_name=None)
        else:
            parent_id = cache.categories.get(parent_name, None)
            # Если айди родителя содержится в кеше
            if parent_id:
                db_id = catalog_db.add_new_category(name=category_name, parent_id=parent_id)
            else:
                db_id = catalog_db.add_new_category(name=category_name, parent_name=parent_name)

        cache.categories[category_name] = db_id
        return db_id


def save_manufacturer_update_cache(session_factory, cache, trademark, full_name, country):
    with session_factory() as session:
        catalog_db = CatalogCRUD(session)
        db_id = catalog_db.add_new_manufactory(trademark=trademark, full_name=full_name, country=country)
        cache.manufacturers[full_name] = db_id
        return db_id

def save_product(session_factory, manufacturer_id, name, description, composition, storage_info, unit):
    with session_factory() as session:
        catalog_db = CatalogCRUD(session)
        db_id = catalog_db.add_new_product(
            manufacturer_id=manufacturer_id,
            name=name,
            description=description,
            composition=composition,
            storage_info=storage_info,
            unit=unit
        )
        return db_id

def save_product_display_update_cache(session_factory, cache, source, product_id, article):
    with session_factory() as session:
        catalog_db = CatalogCRUD(session)
        catalog_db.add_new_product_display(source=source, product_id=product_id, article=article)
        cache.product_display[article] = product_id
        return product_id

def save_property_update_cache(session_factory, cache, name, group):
    with session_factory() as session:
        catalog_db = CatalogCRUD(session)
        db_id = catalog_db.add_new_property(name=name, group=group)
        cache.properties[name] = db_id
        return db_id


def main():
    spider = Spider()
    # Создаем фабрику сессий
    session_factory = get_session_factory()
    cache = get_cache(session_factory)


    """
    Мы имеем класс CatalogCRUD, который требует сессию для создания. Это нормальная практика, 
    так называемый паттерн "Unit of Work". Управление жизненным циклом сессии (создание, коммит, закрытие) должно быть 
    отделено от класса CRUD. Поэтому создаём сессию в менеджере контекста и для каждой сессии создаём объект CatalogCRUD
    """

    for product in spider.crawl():

        # Проверяем, есть ли артикул товара в кеше. Если нет - добавляем все данные по товару в БД
        if not cache.product_display.get(product.productId, None):

            # manufacturer
            if product.legalInfo:
                # manufacturerName - key in cache
                if not cache.manufacturers.get(product.legalInfo.manufacturerName, None):
                    if product.legalInfo.trademarkName:
                        trademark = product.legalInfo.trademarkName
                    else:
                        trademark = product.legalInfo.title

                    save_manufacturer_update_cache(session_factory, cache, trademark,
                                            product.legalInfo.manufacturerName, product.legalInfo.countryOfManufacture
                                            )
            # product\product-display
            manufacturer_id = cache.manufacturers[product.legalInfo.manufacturerName]
            product_id = save_product(session_factory=session_factory,
                                      manufacturer_id=manufacturer_id,
                                      name=product.productName,
                                      description=product.description.productDescription,
                                      composition=product.description.composition,
                                      storage_info=product.description.storagePeriod,
                                      unit=product.quantityInfo.quantityInOrder)
            save_product_display_update_cache(session_factory, cache, 'edostavka.by', product_id, product.productId)

            # categories
            if product.categories:
                for i, category in enumerate(product.categories):
                    if not cache.categories.get(category, None):
                        parent_name = product.categories[i - 1] if i != 0 else None
                        save_category_update_cache(session_factory, cache, category, parent_name)
                    category_id = cache.categories[category]


            # properties
            if product.additionalProperties:
                for group_property in product.additionalProperties:
                    for group_name in group_property.groupProperty:
                        if not cache.properties.get(group_name.propertyName, None):
                            save_property_update_cache(session_factory, cache,
                                                                     group_name.propertyName, group_property.groupName)

                        property_id = cache.properties[group_name.propertyName]
                        product_id = cache.product_display[product.productId]
                        with session_factory() as session:
                            catalog_db = CatalogCRUD(session)
                            for property_value in group_name.propertyValue:
                                catalog_db.add_new_product_property(product_id, property_id, property_value)


if __name__ == "__main__":
    main()