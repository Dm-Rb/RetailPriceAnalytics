from sqlalchemy.orm import sessionmaker
from .engine import create_db_engine
from .models.base import Base

def get_session_factory():
    engine = create_db_engine()
    Base.metadata.create_all(bind=engine)  # create tables if its not exist
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Для dependency injection в веб-приложении
def get_db():
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()