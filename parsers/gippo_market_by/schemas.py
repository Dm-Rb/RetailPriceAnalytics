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
    categories:  Optional[List[Breadcrumb]] = Field(None, alias="breadcrumbs") # зачение None принимается при отсутствии ключа breadcrumbs в передаваемом для парсинга документе

    @model_validator(mode="after")  # Валидатор после создания поля.
    # Вот такой варик не сработает без @model_validator -> manufactory = Manufacturer.from_properties(self.properties)
    def build_manufactory(self):
        self.manufactory = Manufacturer.from_properties(self.properties)
        # удаляем связанные ключи из properties
        for key in ("nameManufacturer", "nameCountry", "brandText"):
            if key in self.properties.root:
                del self.properties.root[key]
        return self

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

    def add_main_category(self, category_title: str, category_slug: str) -> Optional[Breadcrumb]:
        """Ответ с деталями продукта приходит с не всегда полным списком категорий. Данный метод добавляет во внешнем
            методе парсера главную категорию (текущую по итерации) в список Product.categories"""
        titles_list = [i.title for i in self.categories]
        if category_title not in titles_list:
            new_category = Breadcrumb(
                title=category_title,
                slug=category_slug,
                parent_title=None
            )
            self.categories.append(new_category)
        return None

