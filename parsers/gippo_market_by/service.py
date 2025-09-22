from database.crud.catalog import CatalogCRUD
from parsers.gippo_market_by.cache import Cache
from slugify import slugify
import hashlib


class CategoryService(Cache):
    def __init__(self, session_factory):
        super().__init__()
        self.__session_factory = session_factory  # фабрика сессий

        # Заполняем кеши из базы данных
        with session_factory() as session:
            catalog_db = CatalogCRUD(session)
            # categories
            for item in catalog_db.get_all_categories():
                self.categories.setdefault(item.name, item.id)
            # manufacturers
            for item in catalog_db.get_all_manufacturers():
                # преобразуем записи из бд в строковый хеш
                self.manufacturers.setdefault(self.string_hash(item.full_name), item.id)
            # properties
            for item in catalog_db.get_all_properties():
                self.properties.setdefault(item.name, item.id)
            # product_articles
            source = 'gippo-market.by'
            for item in catalog_db.get_all_product_display_by_source(source):
                self.product_display.setdefault(item.article, item.product_id)

    @staticmethod
    def string_hash(string):
        if not string:
            return None
        string = slugify(string)
        string = string.replace('_', '')
        string = string.replace('-', '')
        if len(string) > 16:
            text_bytes = string.encode('utf-8')

            hash_object = hashlib.new('sha256')
            hash_object.update(text_bytes)
            string = hash_object.hexdigest()

        return string

    def get_product_id(self, manufacturer_id, name, description, composition, storage_info, unit, barcode):
        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            product_id = catalog_db.save_new_product(
                manufacturer_id=manufacturer_id,
                name=name,
                description=description,
                composition=composition,
                storage_info=storage_info,
                unit=unit,
                barcode=barcode
            )
        return product_id

    def get_category_id(self, category_name, parent_name):
        if self.categories.get(category_name, None):
            return self.categories[category_name]

        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)

            if not parent_name:
                category_id = catalog_db.save_new_category(name=category_name, parent_id=None, parent_name=None)
                self.categories.setdefault(category_name, category_id)  # put to cache
                return category_id

            else:
                # Если айди родителя содержится в кеше
                parent_id = self.categories.get(parent_name, None)
                if parent_id:
                    category_id = catalog_db.save_new_category(name=category_name, parent_id=parent_id)
                else:
                    category_id = catalog_db.save_new_category(name=category_name, parent_name=parent_name)
        self.categories.setdefault(category_name, category_id)  # put to cache
        return category_id

    def get_manufactory_id(self, trademark, full_name, country):

        manufactory_hash = self.string_hash(f"{trademark if trademark else ''}{full_name if full_name else ''}")
        if self.manufacturers.get(manufactory_hash, None):
            return self.manufacturers[manufactory_hash]

        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            manufactory_id = catalog_db.save_new_manufactory(trademark=trademark, full_name=full_name, country=country)
        self.manufacturers.setdefault(manufactory_hash, manufactory_id)
        return manufactory_id

    def get_property_id(self, name, group=None):
        if self.properties.get(name, None):
            return self.properties[name]

        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            property_id = catalog_db.save_new_property(name, group)
        self.properties.setdefault(name, property_id)
        return property_id

    def get_product_display_id(self, product_id: int, display: str, source: str):
        if self.product_display.get(display, None):
            return self.product_display[str(display)]

        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            product_display_id = catalog_db.get_product_display_id(product_id=product_id,
                                                                   article=display,
                                                                   source=source)
        if product_display_id:
            return product_display_id[0]

    def save_product_category_relations(self, product_id: int, categories_id: list[id]):
        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            catalog_db.save_product_category_relations(product_id, categories_id)

    def save_product_display_relations(self, source, product_id, display):
        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            product_display_id = catalog_db.save_product_article_relations(source=source,
                                                                           product_id=product_id,
                                                                           article=display)
        self.product_display[display] = product_id
        return product_display_id  # table pf key

    def save_product_property_values_relations(self, product_id: int, property_id: int, values_list: list):
        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            catalog_db.save_product_property_value_relations(product_id=product_id,
                                                             property_id=property_id,
                                                             values=values_list)

    def save_product_images_relations(self, product_id: int, image_urls_list: list):
        if not image_urls_list:
            return
        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            catalog_db.save_product_images_relations(product_id=product_id,
                                                     images=image_urls_list)

    def save_product_price(self, product_display_id: int, price: float, date_time: str):
        if not price:
            return
        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            catalog_db.save_product_price_datetime_relations(product_display_id=product_display_id,
                                                             price=price,
                                                             date_time=date_time)
