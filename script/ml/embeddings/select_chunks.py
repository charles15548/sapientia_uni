import os
import numpy as np
from script.ml.embeddings.embedding import generar_embedding  # Usa tu función existente
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv
load_dotenv()
# Config DB
VECTORES_CACHE = None
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def historial_a_texto(historial, max_mensajes = 6):
    mensajes = historial[-max_mensajes:]

    return "\n".join(
        f"{'Usuario' if m.rol == 'user' else 'Asistente'}: {m.contenido}"
        for m in mensajes
    )

def construir_query_embedding(pregunta_usuario, historial):
    historial_texto = historial_a_texto(historial)
    if historial_texto.strip():
        return f"""
            Contexto de la Conversación:
            {historial_texto}
            Pregunta actual:
            {pregunta_usuario}
        """
    return pregunta_usuario



def select_chunck(pregunta,historial, cantidad_chunks):
    query_embedding = construir_query_embedding(pregunta, historial)
    session = SessionLocal()

    try:
        embedding = generar_embedding(query_embedding)

        if isinstance(embedding, np.ndarray):
            embedding = [float(x) for x in embedding]

        query = text("""
            SELECT 
                dc.id_libro,
                l.libro AS nombre_libro,
                l.fecha,
                l.autor,
                dc.contenido,
                dc.pagina
            FROM document_chunks dc
            JOIN libros l ON l.id = dc.id_libro
            WHERE 
                dc.embedding  IS NOT NULL    
                AND trim(coalesce(dc.contenido, '')) <> ''
            ORDER BY dc.embedding <=> (:pregunta)::vector
            LIMIT :cantidad
        """)

        session.execute(text("SET ivfflat.probes = 10"))

        result = session.execute(
            query,
            {
                "pregunta": embedding,
                "cantidad": cantidad_chunks
            }
        ).fetchall()

        if not result:
            return []

        return [
            {
                "contenido": r.contenido,
                "libro": r.nombre_libro,
                "pagina": r.pagina,
                "id_libro": r.id_libro,
                "fecha": r.fecha,
                "autor": r.autor
               
            }
            for r in result
        ]

    except Exception as e:
        print(f"❌ Error en select_chunck: {e}")
        return []

    finally:
        session.close()











