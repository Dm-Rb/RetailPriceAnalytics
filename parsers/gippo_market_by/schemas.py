from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, RootModel, model_validator


class PropertyItem(BaseModel):
    code: str
    type: str
    value: Union[str, int, float, bool, None]
    name: Optional[str] = None
    group: Optional[str] = None

    @model_validator(mode="after")
    def set_group(self):
        if self.group is None:
            if self.code in ["fats", "proteins", "energy", "energyJ", "carbohydrates"]:
                self.group = "Пищевая ценность"
            else:
                self.group = "Основные характеристики"
        return self


class Properties(RootModel[Dict[str, PropertyItem]]):
    def __getitem__(self, item: str) -> PropertyItem:
        return self.root[item]

    def get(self, key: str, default=None):
        return self.root.get(key, default)

    def keys(self):
        return self.root.keys()

    def values(self):
        return self.root.values()

    def items(self):
        return self.root.items()


class Manufacturer(BaseModel):
    name: Optional[str]
    country: Optional[str]
    trademark: Optional[str]

    @classmethod
    def from_properties(cls, properties):
        """
        Принимает Product.properties. Это словарь с ключами == PropertyItem.code
        """
        # извлекаем PropertyItem по ключам, которые идентичны PropertyItem.code
        name_item = properties.get("nameManufacturer")
        country_item = properties.get("nameCountry")
        trade_mark = properties.get("brandText")

        # возвращает новый экземпляр класса с аттрибутами name= nameManufacturer.value, country=nameCountry.value и т.д
        return cls(
            name=name_item.value if name_item else None,
            country=country_item.value if country_item else None,
            trademark=trade_mark.value if trade_mark else None
        )


class Breadcrumb(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    parent_title: str | None = Field(default=None, exclude=True)  # Исключаем из сериализации, это поле пустое и не парсится из входных данных


class Proposal(BaseModel):
    price: float

class Market(BaseModel):
    proposal: Proposal


class ResponseModel(BaseModel):
    markets: List[Market]


class Product(BaseModel):
    id: str
    slug: str
    name: str = Field(..., alias="title")
    barcode: str | None
    description: str | None
    unit: str | None = Field(..., alias="short_name_uom")
    properties: Properties  # Не используется. Но его необходимо проинициализировать, для юза в других полях
    images: List[str] | None
    manufactory: Optional[Manufacturer] = None   # 👈 объявляем поле (если присваивать напрямую, получится хуета

    @model_validator(mode="after")  # Валидатор после создания поля.
    # Вот такой варик не сработает без @model_validator -> manufactory = Manufacturer.from_properties(self.properties)
    def build_manufactory(self):
        self.manufactory = Manufacturer.from_properties(self.properties)
        # удаляем связанные ключи из properties
        for key in ("nameManufacturer", "nameCountry", "brandText"):
            if key in self.properties.root:
                del self.properties.root[key]
        return self

    categories:  Optional[List[Breadcrumb]] = Field(None, alias="breadcrumbs") # зачение None принимается при отсутствии ключа breadcrumbs в передаваемом для парсинга документе

    @model_validator(mode='after')
    def set_default_categories(self) -> 'Product':
        # Если categories не установлено, создаем список с одним Breadcrumb с None значениями
        if self.categories is None:
            self.categories = [Breadcrumb(title=None, slug=None, parent_title=None)]
        # Если categories есть, но это пустой список, добавляем элемент с None
        elif self.categories == []:
            self.categories = [Breadcrumb(title=None, slug=None, parent_title=None)]
        return self

    markets: List[Market]


# # пример использования
# data = \
# {'id': '9b544347-a262-4746-90cd-c65e768cc9ba', 'barcode': '4696666999695', 'title': 'Скатерть одноразовая 110х140 см ', 'slug': 'skatert-odnorazovaya-110h140-sm', 'description': None, 'is_viewed': False, 'images': ['https://app.willesden.by/images/4696666999695.jpg'], 'short_name_uom': 'ШТ', 'container_with_another': 0, 'properties': {'width': {'code': 'width', 'name': 'Ширина, мм', 'type': 'number', 'value': 200, 'multiple': 'N'}, 'height': {'code': 'height', 'name': 'Высота, мм', 'type': 'number', 'value': 350, 'multiple': 'N'}, 'length': {'code': 'length', 'name': 'Глубина, мм', 'type': 'number', 'value': 10, 'multiple': 'N'}, 'brandText': {'code': 'brandText', 'name': 'Бренд', 'type': 'string', 'value': 'Vip', 'multiple': 'N'}, 'containsGMO': {'code': 'containsGMO', 'name': 'Содержит ГМО', 'type': 'bool', 'value': 0, 'multiple': 'N'}, 'grossWeight': {'code': 'grossWeight', 'name': 'Вес брутто, кг', 'type': 'number', 'value': 0.1, 'multiple': 'N'}, 'nameCountry': {'code': 'nameCountry', 'name': 'Страна', 'type': 'string', 'value': 'РОССИЯ', 'multiple': 'N'}, 'nameImporter': {'code': 'nameImporter', 'name': 'Импортер в РБ', 'type': 'string', 'value': 'ИУП "БелВиллесден",220024, г. Минск, пер. Асаналиева, 3, ком.20', 'multiple': 'N'}, 'nameManufacturer': {'code': 'nameManufacturer', 'name': 'Производитель', 'type': 'string', 'value': '-', 'multiple': 'N'}, 'short_name_uom': {'code': 'short_name_uom', 'name': 'Единицы измерения', 'type': 'string', 'value': 'ШТ', 'multiple': 'N'}}, 'meta': {'title': 'Скатерть одноразовая 110х140 см ', 'description': None}, 'markets': [{'id': 73, 'title': 'ГИППО  г. Минск, пр-т Рокоссовского, 2', 'longitude': 27.59487, 'latitude': 53.87502, 'address': 'г. Минск, пр-т Рокоссовского, 2', 'phone_number': '+375173670046', 'pick_up_phone_number': '+375445056110', 'is_new': False, 'working_hours': [['08:00', '23:59'], ['08:00', '23:59'], ['08:00', '23:59'], ['08:00', '23:59'], ['08:00', '23:59'], ['08:00', '23:59'], ['08:00', '23:59']], 'opening_hours': [['10:00', '22:00'], ['10:00', '22:00'], ['10:00', '22:00'], ['10:00', '20:00'], ['10:00', '22:00'], ['10:00', '22:00'], ['10:00', '22:00']], 'opened': False, 'market_opened': False, 'city': 'Минск', 'proposal': {'price': 1.57, 'max_qty': 25, 'ignore_max_qty': 0, 'is_promo': 0, 'promo_price_before': None, 'promo_title': 'Акция', 'promo_id': None, 'promo_color': None}, 'available_timeslots': ['2025-09-14 10:00:00', '2025-09-14 10:30:00', '2025-09-14 11:00:00', '2025-09-14 11:30:00', '2025-09-14 12:00:00', '2025-09-14 12:30:00', '2025-09-14 13:00:00', '2025-09-14 13:30:00', '2025-09-14 14:00:00', '2025-09-14 14:30:00', '2025-09-14 15:00:00', '2025-09-14 15:30:00', '2025-09-14 16:00:00', '2025-09-14 16:30:00', '2025-09-14 17:00:00', '2025-09-14 17:30:00', '2025-09-14 18:00:00', '2025-09-14 18:30:00', '2025-09-14 19:00:00', '2025-09-14 19:30:00', '2025-09-14 20:00:00', '2025-09-14 20:30:00', '2025-09-14 21:00:00', '2025-09-14 21:30:00'], 'product_count': '19892', 'nearest_available_timeslot': '2025-09-14 02:00:00'}], 'is_package': False, 'pass_scales_step': None, 'age_restrict': None, 'over_sales_limit': None, 'stickers': [], 'meta_categories': ['Спортивные товары и отдых', 'Грили и мангалы', 'Одноразовая посуда'], 'breadcrumbs': [{'title': 'Спортивные товары и отдых', 'slug': 'sportivnye-tovary-i-otdyh'}, {'title': 'Грили и мангалы', 'slug': 'grili-i-mangaly'}, {'title': 'Одноразовая посуда', 'slug': 'odnorazovaya-posuda'}]}
#
# #
# #
# product = Product(**d)
# print(product.description)
