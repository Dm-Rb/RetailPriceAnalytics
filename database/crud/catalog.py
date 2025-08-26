from sqlalchemy.orm import Session
from database.models.catalog import Category, Manufactory, ProductDisplay
from typing import Union


class CatalogCRUD:

    def __init__(self, session: Session):
        self.session = session

    def get_all_categories(self):
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

        new_category = Category(
                name=name,
                parent_id=parent_id
                    )
        self.session.add(new_category)
        self.session.commit()

        return new_category.id

    def get_all_manufacturers(self):
        return self.session.query(Manufactory).all()

    def add_new_manufactory(self,
                            full_name: str,
                            trademark: Union[str, None] = None,
                            country: Union[str, None] = None
                            ) -> Manufactory.id:

        new_manufactory = Manufactory(
                trademark=trademark,
                full_name=full_name,
                country=country
                    )
        self.session.add(new_manufactory)
        self.session.commit()

        return new_manufactory.id

    def get_all_product_display_by_source(self, source: str):
        return self.session.query(ProductDisplay).filter(ProductDisplay.source == source).all()



