from sqlalchemy import create_engine
from dotenv import load_dotenv
import os


def get_database_url():
    load_dotenv()
    database_url = (
        f"{os.getenv('DB_DRIVER')}:"
        f"//{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )
    return database_url


def create_db_engine():
    url = get_database_url()
    echo = os.getenv("DB_ECHO", "False").lower() == "true"

    engine = create_engine(url, echo=echo, future=True)
    return engine
