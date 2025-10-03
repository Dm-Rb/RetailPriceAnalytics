from sqlalchemy.orm import sessionmaker
from database.engine import create_db_engine
from database.models.base import Base
from sqlalchemy import text, event


def get_session_factory(schema_name: str):
    if not schema_name:
        raise ValueError('Schema_name is None')

    # Импортируем модели, чтобы таблицы попали в Base.metadata
    import database.models.catalog

    engine = create_db_engine()

    # создаём схему и таблицы
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        conn.execute(text(f'SET search_path TO "{schema_name}"'))
        Base.metadata.create_all(bind=conn)

    # listener для будущих сессий
    """
    Listener — это механизм «событий» (event system) в SQLAlchemy. 
    Он позволяет подписаться на определённые действия движка, соединения или сессии и выполнять свой код, 
    когда это действие происходит.
    """
    @event.listens_for(engine, "connect", insert=True)
    def _set_search_path(dbapi_connection):
        with dbapi_connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema_name}"')

    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
