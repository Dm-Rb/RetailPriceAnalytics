from sqlalchemy.orm import Session
from database.models.catalog import Category, Manufactory, ProductDisplay, Product, Property, ProductPropertyValue
from typing import Union


class CatalogCRUD:

    def __init__(self, session: Session):
        self.session = session

    def get_all_categories(self) -> list:
        return self.session.query(Category).all()

    def add_new_category(self, name: str,
                         parent_id: Union[int, None] = None,
                         parent_name: Union[str, None] = None
                         ) -> Category.id:
        # если передан parent_name -> искать его id
        if parent_name:
            parent_id = self.session.query(Category.id).filter(Category.name == parent_name).first().get('id', None)
            if not parent_id:
                raise ValueError('No <parent_id> found for the provided <parent_name>')

        new_row = Category(
                name=name,
                parent_id=parent_id
                    )
        self.session.add(new_row)
        self.session.commit()

        return new_row.id

    def get_all_manufacturers(self) -> list:
        return self.session.query(Manufactory).all()

    def add_new_manufactory(self,
                            full_name: str,
                            trademark: Union[str, None] = None,
                            country: Union[str, None] = None
                            ) -> Manufactory.id:

        new_row = Manufactory(
                trademark=trademark,
                full_name=full_name,
                country=country
                    )
        self.session.add(new_row)
        self.session.commit()

        return new_row.id

    def add_new_product(self,
                        manufacturer_id: int,
                        name: str,
                        barcode: Union[str, None] = None,
                        description: Union[str, None] = None,
                        composition: Union[str, None] = None,
                        storage_info: Union[str, None] = None,
                        unit: Union[str, None] = None
                        ) -> Product.id:

        new_row = Product(
            manufacturer_id=manufacturer_id,
            name=name,
            barcode=barcode,
            description=description,
            composition=composition,
            storage_info=storage_info,
            unit=unit
        )
        self.session.add(new_row)
        self.session.commit()

        return new_row.id

    def get_all_product_display_by_source(self, source: str) -> list:
        return self.session.query(ProductDisplay).filter(ProductDisplay.source == source).all()

    def add_new_product_display(self, source: str, product_id: int, article: str) -> ProductDisplay.id:
        new_row = ProductDisplay(source=source, product_id=product_id, article=article)
        self.session.add(new_row)
        self.session.commit()

        return new_row.id

    def get_all_properties(self) -> list:
        return self.session.query(Property).all()

    def add_new_property(self, name: str, group: Union[str, None]=None):
        new_row = Property(name=name, group=group)
        self.session.add(new_row)
        self.session.commit()
        return new_row.id

    def add_new_product_property(self, product_id: int, property_id: int, value: Union[str, None]=None):
        new_row = ProductPropertyValue(product_id=product_id, property_id=property_id, value=value)
        self.session.add(new_row)
        self.session.commit()
        return new_row.id
