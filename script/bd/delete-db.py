# drop_tables.py
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def drop_tables():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS persona CASCADE; DROP TABLE IF EXISTS libros CASCADE; DROP TABLE IF EXISTS document_chunks CASCADE;"))
        conn.commit()
        print("🗑️ Tablas eliminada correctamente.")

if __name__ == "__main__":
    drop_tables()
