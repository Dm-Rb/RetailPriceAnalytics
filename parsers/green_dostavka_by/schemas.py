from pydantic import BaseModel, model_validator, Field
import json
from typing import List, Optional, Union


class Category(BaseModel):
    productsViewType: str
    parentId: Optional[Union[int, str, None]]
    id: int
    name: str = Field(..., alias="title")
    slug: str
    path: str


class Categories(BaseModel):
    categories: List[Category]
    cash_id: dict | None = Field(default=None, exclude=True)  # это поле пустое и не парсится из входных данных

    @model_validator(mode="before")
    @classmethod
    def __extract_and_transform(cls, values):
        """
        Преобразует Входные данные в список словарей
        """
        props = values.get('props', None)
        if not props:
            raise ValueError('"catalog_data" does not contain "props" key')
        initial_state = props.get('initialState', None)
        if not initial_state:
            raise ValueError('"catalog_data > props" does not "initialState" key')

        # сериализуем <initial_state> как json
        if isinstance(initial_state, str):
            initial_state = json.loads(initial_state)

        initial_state_categories = initial_state.get('categories', None)
        if not initial_state_categories:
            raise ValueError('"catalog_data > props > initialState" does not "categories" key')
        initial_state_categories_data = initial_state_categories.get('data', None)
        if not initial_state_categories_data:
            raise ValueError('"catalog_data > props > initialState > categories" does not "data" key')

        # рекурсивный вызов парсера:
        catalog_map = cls.__parse_catalog_map(initial_state_categories_data[0][1])
        catalog_map = cls.__flatten_array(catalog_map)  # преобразовать в одномерный (плоский) массив
        return {'categories': catalog_map}

    @classmethod
    def __parse_catalog_map(cls, data):
        """
        Рекурсивно преобразует структуру с __iterable: 'Map' и 'List' в обычные dict и list.
        """
        if isinstance(data, dict):
            if data.get("__iterable") == "Map":
                return {k: cls.__parse_catalog_map(v) for k, v in data["data"]}
            elif data.get("__iterable") == "List":
                return [cls.__parse_catalog_map(item) for item in data["data"]]
            else:
                # парсим вложенные элементы, если они есть
                return {k: cls.__parse_catalog_map(v) for k, v in data.items() if k != "__iterable"}
        elif isinstance(data, list):
            return [cls.__parse_catalog_map(item) for item in data]
        else:
            return data

    @classmethod
    def __flatten_array(cls, arr):
        """
        Преобразует древовидную структуру в плоский список
        """
        result = []
        for item in arr:
            if item['productsViewType'] != "NORMAL":
                continue
            result.append(item)
            if 'children' in item and item.get('children', None):
                result.extend(cls.__flatten_array(item['children']))
        return result

    @model_validator(mode="after")
    def __fill_parent_names(self):
        """
        Заполняет parent_name для каждой категории на основе parentId
        """
        # cоздаем словарь, где ключ - id категории, значение - объект Category. Что то вроде кеша для быстрого поиска
        categories_dict = {self.categories[i].id: i for i in range(len(self.categories))}
        self.cash_id = categories_dict  # ключ - id категории, значение - индекс категории в списке categories

        return self

    def get_item_by_id(self, id_):
        index = self.cash_id[id_]
        return self.categories[index]

    def get_parents(self, parent_id, parents_list=None):
        # Этот метод по parent_id подтягивает список всех родителей категории
        if not parents_list:
            parents_list = []
        index = self.cash_id[parent_id]
        parent = self.categories[index]
        parents_list.append(parent.name)
        if parent.parentId:
            return self.get_parents(parent.parentId, parents_list)
        return parents_list


class StoreProduct(BaseModel):
    price: Union[int, float, None]
    priceWithSale: Union[int, float, None]

    @model_validator(mode="after")
    # Добавляем хост в начало и разрешение изображения
    def add_host(self):
        if self.price:
            self.price = self.price / 100
        if self.priceWithSale:
            self.priceWithSale = self.priceWithSale / 100

        return self


class Property(BaseModel):
    name: str | None = Field(default=None, alias="name")
    value: Union[str, int, float, None]
    group: Optional[str]


class Product(BaseModel):
    id: int | str = Field(default=None, alias="id")
    article: str = Field(default=None, alias="vendorCode")
    slug: str
    name: str | None = Field(default=None, alias="title")
    unit: str | None = Field(..., alias="quantityLabel")
    barcode: str | None = Field(default=None, alias="gtin")
    storage_info: str | None = Field(default=None, alias="storageConditions")
    composition: str | None
    # description: str | None = None
    manufacturer_name: str | None = Field(default=None, alias="producer")
    manufacturer_country: str | None = Field(default=None, alias="producingCountry")
    manufacturer_trademark: str | None = Field(..., alias="brand")
    prices: StoreProduct | None = Field(alias="storeProduct")
    images: List
    properties: List[Property]
    categoriesIds: List[int]
    categories_: None | List = Field(default=[], exclude=True)


    @model_validator(mode="before")
    @classmethod
    def preparing_data(cls, incoming_data: dict):  # values — это сырые данные, переданные в  Product, Product(-> **data)
        """
        Подготавливает сырые данные для валидации.
        """

        # Создаём отдельный ключ <properties> в входящем агументе, заполняем его данными
        incoming_data['properties'] = []
        volume = incoming_data.get('volume', None)
        if volume:
            incoming_data['properties'].append(
                {'name': 'Количество',
                 'value': volume,
                 'group': 'Основные характеристики'}
            )
        ###
        energy_cost = incoming_data.get('energyCost', None)
        if energy_cost:
            incoming_data['properties'].append({'name': "Пищевая ценность",
                                                "value": energy_cost,
                                                "group": "Пищевая ценность"})
        ####
        files = incoming_data.get('files')
        incoming_data['images'] = []
        if files:
            file_storage_host = "https://io.activecloud.com/static-green-market"
            for filename in files:
                filename = filename.get('filename')
                if filename:
                    incoming_data['images'].append(f"{file_storage_host}/{'1400x1400-'}{filename}")
        ###
        if incoming_data.get('brand'):
            incoming_data['brand'] = incoming_data['brand'].get('title')
        incoming_data['composition'] = incoming_data.get('description', None)

        return incoming_data

    def set_categories(self, categories_obj):
        result = []
        for category_id in self.categoriesIds:
            try:
                category_item = categories_obj.get_item_by_id(category_id)
                patents_list = categories_obj.get_parents(category_item.parentId)
                product_categories: list = [category_item.name] + patents_list
                product_categories.reverse()
                result.append(product_categories)
            except KeyError:
                continue
        self.categories_ = result
        return self
