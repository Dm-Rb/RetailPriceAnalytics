from typing import List, Optional, Union
from pydantic import BaseModel, Field, model_validator


class Property(BaseModel):
    code: str
    value: Union[str, int, float, None]
    name: str | None = Field(default=None, alias="name")
    group: Optional[str] = None
    """
    Аттрибут group не содержится в сыром файле json. Атрибут сформирован со значением None и ниже функция с декоратором 
    model_validator задаёт ему значение в зависимости от значений аттрибута code     
    """
    @model_validator(mode="after")
    def set_group(self):
        if self.group is None:
            if self.code in ["fats", "proteins", "energy", "energyJ", "carbohydrates"]:
                self.group = "Пищевая ценность"
            else:
                self.group = "Основные характеристики"
        return self


class Manufacturer(BaseModel):
    name: Optional[str]
    country: Optional[str]
    trademark: Optional[str]


class Breadcrumb(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    parent_title: str | None = Field(default=None, exclude=True)  # это поле пустое и не парсится из входных данных


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
    storage_info: str | None
    unit: str | None = Field(..., alias="short_name_uom")
    images: List[str] | None
    properties: List[Property]
    manufacturer: Optional[Manufacturer]
    categories: List[Breadcrumb] = Field(None, alias="breadcrumbs")
    price: str | float | None

    @model_validator(mode="before")
    def transform_properties(cls, values: dict):  # values — это сырые данные, переданные в  Product, Product(-> **data)
        """
        Этот декоратор позволяет функции предобработать сырые данные до того, как они
        будут провалидированы и собраны в модель. В данном случае мы преобразуем запутанный словарь по ключу <properties>
        в понятный и легкочитаемый список. Т.е при валидации сырые данные будут соответствовать properties: List[Property]
        Так же выдёргиваем определённые значения из properties и помещаем их с отдельными ключами
        """
        props = values.get("properties")

        # если properties нет или это не dict, просто возвращаем как есть
        if not isinstance(props, dict):
            return values

        properties_list = []
        # вычленяем всё, что связано с производителем и выносим в отдельный ключ
        manufacturer = {'trademark': None, 'country': None, 'name': None}
        values['storage_info'] = None  # -> Product.storage_info
        for prop in props.values():
            if prop.get("code") == 'short_name_uom':
                # параметр "Единицы измерения" уже вынесен как отдельный аттрибут Product.unit, поэтому не включаем его
                continue
            # Значения, связанные с производителем не включаем в properties_list, а выносим в отдельный словарь
            if prop.get("code") == 'brandText':
                manufacturer['trademark'] = prop.get("value")
                continue
            if prop.get("code") == 'nameCountry':
                manufacturer['country'] = prop.get("value")
                continue
            if prop.get("code") == 'nameManufacturer':
                manufacturer['name'] = prop.get("value")
                continue
            # Игнорируем параметр с ГМО, он не нужен
            if prop.get("code") == "containsGMO":
                continue
            # Выносим отдельно условия храненя
            if prop.get("code") == "conditionsText":
                values['storage_info'] = f"{prop.get('name') or ''}: {prop.get('value') or ''}"
                # if  values['storage_info'] == "" -> values['storage_info'] = None
                if not values['storage_info']:
                    values['storage_info'] = None
                continue
            # Игнорируем параметр импортёра
            if prop.get("code") == 'nameImporter':
                continue

            properties_list.append({
                "code": prop.get("code"),
                "type": prop.get("type"),
                "name": prop.get("name") or prop.get(prop.get("code")),
                "value": str(prop.get("value")),
            })

        values["properties"] = properties_list
        values['manufacturer'] = manufacturer
        values['price'] = None
        for market in values.get('markets', []):
            proposal = market.get('proposal', None)
            if proposal:
                values['price'] = proposal.get('price', None)
                break

        return values

    def add_main_category(self, category_title: str, category_slug: str) -> Optional[Breadcrumb]:
        """Ответ с деталями продукта приходит с не всегда полным списком категорий. Данный метод добавляет во внешнем
            методе парсера главную категорию (текущую по итерации) в список Product.categories"""
        if self.categories is None:
            self.categories = [Breadcrumb(title=category_title, slug=category_slug, parent_title=None)]
            return
        titles_list = [i.title for i in self.categories]
        if category_title not in titles_list:
            new_category = Breadcrumb(
                title=category_title,
                slug=category_slug,
                parent_title=None
            )
            self.categories.append(new_category)
        return
