import os

import dotenv
import psycopg2

dotenv.load_dotenv()


def get_db_connection():
    pool = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
    )
    return pool
