
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey,Date,Boolean,String,text
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector 

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=500,
    connect_args={"sslmode": "require"}
)
Base = declarative_base()

class Persona(Base):
    __tablename__ = "persona"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(Text)
    apellidos = Column(Text)
    correo = Column(Text)
    contrasena = Column(Text)
    foto = Column(Text)


class Libros(Base):
    __tablename__ = "libros"
    id = Column(Integer, primary_key=True, autoincrement=True)
    libro = Column(Text,nullable=False)
   
    fecha = Column(Text)
    autor = Column(Text)
    tipo = Column(Text)
    tags = Column(Text)
    url_doc = Column(Text)

    document_chunks = relationship("DocumentChunks",back_populates="libros", cascade="all, delete-orphan")
    capitulos = relationship(
        "Capitulos",
        back_populates="libro",
        cascade="all, delete-orphan"
    )
class Capitulos(Base):
    __tablename__ = "capitulos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_libro = Column(
        Integer,
        ForeignKey("libros.id", ondelete="CASCADE"),
        nullable=False
    )
    titulo = Column(Text, nullable=False)
    orden = Column(Integer, default=0)
    libro = relationship("Libros", back_populates="capitulos")
    subcapitulos = relationship(
        "Subcapitulos",
        back_populates="capitulo",
        cascade="all, delete-orphan",
        order_by="Subcapitulos.orden"
    )

class Subcapitulos(Base):
    __tablename__ = "subcapitulos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_capitulo = Column(
        Integer,
        ForeignKey("capitulos.id", ondelete="CASCADE"),
        nullable=False
    )
    titulo = Column(Text, nullable=False)
    orden = Column(Integer, default=0)
    capitulo = relationship("Capitulos",back_populates="subcapitulos")


class DocumentChunks(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_libro = Column(Integer,ForeignKey("libros.id", ondelete="CASCADE"),nullable=False)
    id_capitulo = Column(
        Integer,ForeignKey("capitulos.id", ondelete="SET NULL"),nullable=True)
    contenido = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    pagina = Column(Text, nullable=False)
    libros = relationship("Libros", back_populates="document_chunks")




# def migrar_subcapitulos():
#     with engine.begin() as conn:
#         caps = conn.execute(text("SELECT id, titulo FROM capitulos")).fetchall()

#         for cap in caps:
#             partes = cap.titulo.split("\n\n", 1)
#             titulo_limpio = partes[0].strip()

#             conn.execute(
#                 text("UPDATE capitulos SET titulo = :titulo WHERE id = :id"),
#                 {"titulo": titulo_limpio, "id": cap.id}
#             )

#             if len(partes) > 1:
#                 subs = [
#                     linea.lstrip("- ").strip()
#                     for linea in partes[1].splitlines()
#                     if linea.strip()
#                 ]
#                 for orden, sub in enumerate(subs):
#                     conn.execute(
#                         text("""
#                             INSERT INTO subcapitulos (id_capitulo, titulo, orden)
#                             VALUES (:id_capitulo, :titulo, :orden)
#                         """),
#                         {"id_capitulo": cap.id, "titulo": sub, "orden": orden}
#                     )

#     print("✅ Migración completada")

def init_db():
    # 1. Ensure pgvector extension exists
 
    with engine.begin() as conn:
        conn.execute(text('ALTER TABLE capitulos ADD COLUMN IF NOT EXISTS orden INTEGER DEFAULT 0'))
        print('✅ Columna orden agregada a capitulos')
    # with engine.begin() as conn:
    #     conn.execute(text('DROP TABLE IF EXISTS subcapitulos CASCADE'))
    #     print('✅ Tabla subcapitulos eliminada')

    # 2. Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas correctamente con pgvector.")

    # 3. Create regular index
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS document_chunks_id_libro_idx
            ON document_chunks (id_libro);
        """))
        conn.commit()
        print("✅ Índice de id_libro creado")

    # 4. Create vector index with autocommit
    autocommit_engine = engine.execution_options(isolation_level="AUTOCOMMIT")
    with autocommit_engine.connect() as conn:
        conn.execute(text("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS document_chunks_embedding_ivfflat
            ON document_chunks
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 400);
        """))
        print("✅ Índice vectorial ivfflat creado")

if __name__== "__main__":
    init_db()
    
    