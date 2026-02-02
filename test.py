import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

with engine.connect() as conn:
    result = conn.execute(
        text("SELECT vector_dims(embedding) FROM document_chunks LIMIT 5;")
    ).fetchall()

    print("📊 Resultado vector_dims:")
    for r in result:
        print(r[0])
