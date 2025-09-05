from sqlalchemy.orm import sessionmaker
from .engine import create_db_engine
from .models.base import Base
from sqlalchemy import text


def get_session_factory(schema_name=None):
    if not schema_name:
        raise ValueError('Schema_name is None')

    engine = create_db_engine()

    with engine.connect() as conn:
        # Создаем схему если не существует
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        conn.commit()

    # УСТАНАВЛИВАЕМ СХЕМУ ДЛЯ ВСЕХ ТАБЛИЦ МОДЕЛИ (даже если уже установлена)
    for table_name, table in Base.metadata.tables.items():
        table.schema = schema_name

    # СОЗДАЕМ ТАБЛИЦЫ В УКАЗАННОЙ СХЕМЕ
    Base.metadata.create_all(bind=engine)

    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Для dependency injection в веб-приложении
def get_db():
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()