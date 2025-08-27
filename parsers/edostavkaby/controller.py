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
        return


def save_manufacturer_update_cache(session_factory, cache, trademark, full_name, country):
    with session_factory() as session:
        catalog_db = CatalogCRUD(session)
        db_id = catalog_db.add_new_manufactory(trademark=trademark, full_name=full_name, country=country)
        cache.manufacturers[full_name] = db_id
        return

def save_product_display_update_cache(session_factory, cache, product_id, full_name, country):
    with session_factory() as session:
        catalog_db = CatalogCRUD(session)
        db_id = catalog_db.add_new_manufactory(trademark=trademark, full_name=full_name, country=country)
        cache.manufacturers[full_name] = db_id
        return

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
        # categories
        if product.categories:
            for i, category in enumerate(product.categories):
                if not cache.categories.get(category, None):
                    parent_name = product.categories[i - 1] if i != 0 else None
                    processing_category(session_factory, cache, category, parent_name)
        # manufacturer
        if product.legalInfo:
            # manufacturerName - key in cache
            if not cache.manufacturers.get(product.legalInfo.manufacturerName, None):
                if product.legalInfo.trademarkName:
                    trademark = product.legalInfo.trademarkName
                else:
                    trademark = product.legalInfo.title

                processing_manufacturer(session_factory, cache, trademark,
                                        product.legalInfo.manufacturerName, product.legalInfo.countryOfManufacture
                                        )
        # product-display
        if product.productId:
            if not cache.product_display.get(product.productId, None):





        # # properties
        #
        # if product.additionalProperties:
        #     for group in product.additionalProperties:
        #         group_name = group.groupName
        #         print(group_name)
        #         for property in group.groupProperty:
        #             print(property.propertyName)
        input()




if __name__ == "__main__":
    main()
