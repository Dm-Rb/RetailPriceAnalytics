from database.crud.catalog import CatalogCRUD
from parsers.cache import Cache
from slugify import slugify
import hashlib


class CategoryService(Cache):
    def __init__(self, session_factory, source_name: str):
        super().__init__()
        self.__session_factory = session_factory  # фабрика сессий

        # Заполняем кеши из базы данных. Каждое аттрибут Cache это: ключ-имя из таблицы, значение айди из таблицы
        with session_factory() as session:
            catalog_db = CatalogCRUD(session)

            # sources
            for item in catalog_db.get_all_sources():
                self.sources.setdefault(item.name, item.id)

            # если в таблица не содержит строки со значением <source_name> (вход арг при ините) - сделать запись в бд
            self.source_id = self.sources.get(source_name, None)
            if not self.source_id:
                self.source_id = catalog_db.save_new_source(source_name)

            # categories
            for item in catalog_db.get_all_categories(source_id=self.source_id):
                self.categories.setdefault(item.name, item.id)

            # manufacturers
            for item in catalog_db.get_all_manufacturers(source_id=self.source_id):
                # преобразуем записи из бд в строковый хеш (торговое имя + полное имя)
                self.manufacturers.setdefault(self.string_hash((item.trademark or "") + (item.full_name or "")), item.id)

            # articles
            # self.articles = {article: id, article: id, ...}
            for item in catalog_db.get_articles_and_ids_by_source(source_id=self.source_id):
                self.articles.setdefault(item[1], item[0])

            # properties
            for item in catalog_db.get_all_properties():
                self.properties.setdefault(item.name, item.id)

    @staticmethod
    def string_hash(string):
        """
        Хешируем строку для усреднения (что бы при сравнении строк исключить неравенство из-за знаков препинания и тд
        """
        string = slugify(string)
        string = string.replace('_', '')
        string = string.replace('-', '')
        if len(string) > 16:
            text_bytes = string.encode('utf-8')

            hash_object = hashlib.new('sha256')
            hash_object.update(text_bytes)
            string = hash_object.hexdigest()

        return string

    def get_product_id(self, manufacturer_id, name, description, composition, storage_info, unit, article, barcode):
        if self.articles.get(article, None):
            return self.articles[article]

        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            product_id = catalog_db.save_new_product(
                manufacturer_id=manufacturer_id,
                name=name,
                barcode=barcode,
                source_id=self.source_id,
                description=description,
                composition=composition,
                storage_info=storage_info,
                unit=unit,
                source_article=article
            )
        return product_id

    def get_category_id(self, category_name, parent_name):
        if self.categories.get(category_name, None):
            return self.categories[category_name]

        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)

            if not parent_name:
                category_id = catalog_db.save_new_category(name=category_name,
                                                           parent_id=None,
                                                           parent_name=None,
                                                           source_id=self.source_id)
                self.categories.setdefault(category_name, category_id)  # put to cache
                return category_id
            else:
                # Если айди родителя содержится в кеше
                parent_id = self.categories.get(parent_name, None)
                if parent_id:
                    category_id = catalog_db.save_new_category(name=category_name,
                                                               parent_id=parent_id,
                                                               source_id=self.source_id)
                else:
                    category_id = catalog_db.save_new_category(name=category_name,
                                                               parent_name=parent_name,
                                                               source_id=self.source_id)
        self.categories.setdefault(category_name, category_id)  # put to cache
        return category_id

    def get_manufactory_id(self, trademark, full_name, country):
        manufactory_hash = self.string_hash((trademark or "") + (full_name or ""))
        if self.manufacturers.get(manufactory_hash, None):
            return self.manufacturers[manufactory_hash]

        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            manufactory_id = catalog_db.save_new_manufactory(trademark=trademark, full_name=full_name,
                                                             country=country, source_id=self.source_id)
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

    def save_product_category_relations(self, product_id: int, categories_id: list[id]):
        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            catalog_db.save_product_category_relations(product_id, categories_id)

    def save_product_property_values_relations(self, product_id: int, property_id: int, values: list):
        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            catalog_db.save_product_property_values_relations(product_id=product_id,
                                                              property_id=property_id,
                                                              values=values)

    def save_product_images_relations(self, product_id: int, image_urls_list: list):
        if not image_urls_list:
            return
        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            catalog_db.save_product_images_relations(product_id=product_id,
                                                     images=image_urls_list)

    def save_product_price(self, product_id: int, price: float, date_time: str):
        if not price:
            return
        with self.__session_factory() as session:
            catalog_db = CatalogCRUD(session)
            catalog_db.save_product_price_datetime_relations(product_id=product_id,
                                                             price=price,
                                                             date_time=date_time)
