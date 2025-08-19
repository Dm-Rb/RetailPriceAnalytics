from sqlalchemy.orm import sessionmaker
from .engine import create_db_engine


def get_session_factory():
    engine = create_db_engine()
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Для dependency injection в веб-приложении
def get_db():
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()