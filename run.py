from database.crud.catalog import CatalogCRUD
from database.session import get_session_factory
if __name__ == "__main__":
    session_factory = get_session_factory()
    with session_factory() as session:
        # Парсинг и сохранение данных
        catalog_db = CatalogCRUD(session)
        r = catalog_db.get_all_categories()
        catalog_db.add_new_category('Чеснок', parent_name="Овощи")