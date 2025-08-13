from typing import List, Optional
from pydantic import BaseModel, root_validator


class Price(BaseModel):
    basePrice: float | int
    discountedPrice: float | int
    measurePrice: str


class Manufacturer(BaseModel):
    title: str
    manufacturerName: str
    trademarkName: str
    countryOfManufacture: str


class PropertyProduct(BaseModel):
    propertyName: str
    propertyValue: List[str]


class QuantityInfo(BaseModel):
    quantityInBasket: int
    quantitySample: int
    quantityInOrder: int
    quantityInOrderGroupEdit: int
    startOrderFrom: int | float
    division: int | float
    measure: str


class ProductDescription(BaseModel):
    composition: str
    productDescription: str
    storagePeriod: str


class GroupProperty(BaseModel):
    groupName: str | None
    groupProperty: List[PropertyProduct] | None


class Product(BaseModel):
    productId: int
    productName: str
    images: List[str]
    price: Price
    legalInfo: Manufacturer
    previewProperties: List[PropertyProduct]

    # Details fields
    categories: List[str] = []
    quantityInfo: QuantityInfo
    description: ProductDescription
    additionalProperties: List[GroupProperty]
    customPropertyGroup: List[PropertyProduct]

    @root_validator(pre=True)
    def extract_categories(cls, values: dict) -> dict:
        """Извлекает все названия категорий из структуры breadCrumbs"""

        """
        @root_validator(pre=True) указывает, что метод должен выполниться:
        До основной валидации полей (pre=True)
        На уровне всей модели (не для конкретного поля)
        Получает "сырые" входные данные в виде словаря values
        Должен вернуть модифицированный словарь значений
        """
        # https://docs.pydantic.dev/latest/concepts/validators/#model-validators

        breadcrumbs = values.get('breadCrumbs')
        if not breadcrumbs:
            return values

        def recursive_extract(categories: list) -> List[str]:
            """Рекурсивно извлекает названия категорий"""
            names = []
            for item in categories:
                if 'categoryListName' in item:
                    names.append(item['categoryListName'])
                if 'categories' in item and item['categories']:
                    names.extend(recursive_extract(item['categories']))
            return names

        # Извлекаем и сохраняем категории
        values['categories'] = recursive_extract(breadcrumbs)
        return values


class ProductListing(BaseModel):
    pageAmount: int
    pageNumber: int
    products: List[Product]


class ProductData(BaseModel):
    product: Product
