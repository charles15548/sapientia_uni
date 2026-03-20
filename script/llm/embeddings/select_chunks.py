import os
import numpy as np
from script.llm.embeddings.embedding import generar_embedding
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

    # Construir el texto de busqueda convinando pregunta + historial
    # Esto enriquese el embeddings con contexto conversacional
    query_embedding = construir_query_embedding(pregunta, historial)
    session = SessionLocal()

    try:
        #  Convertir el texto a vector numérico (embedding)
        #    Es el "fingerprint semántico" de la pregunta
        embedding = generar_embedding(query_embedding)

        if isinstance(embedding, np.ndarray):
            embedding = [float(x) for x in embedding]

         # --- FASE 1: top  chunks más cercanos globalmente ---
        top_global = """
        top_global AS (
            SELECT 
                dc.id_libro,
                l.libro       AS nombre_libro,
                l.fecha,
                l.autor,
                dc.contenido,
                dc.pagina,
                dc.embedding <=> (:pregunta)::vector AS distancia
            FROM document_chunks dc
            JOIN libros l ON l.id = dc.id_libro
            WHERE 
                dc.embedding IS NOT NULL
                AND trim(coalesce(dc.contenido, '')) <> ''
            ORDER BY dc.embedding <=> (:pregunta)::vector
            LIMIT 100
        )
        """
        # --- FASE 2: ranking interno por libro ---
        ranked = """
        ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY id_libro   -- reinicia contador por cada libro
                    ORDER BY distancia      -- el más cercano es rank 1
                ) AS rank_por_libro
            FROM top_global
        )
        """
        # --- SELECCIÓN FINAL: diversidad de fuentes + relevancia ---
        select_final ="""
        SELECT *
        FROM ranked
        ORDER BY
            distancia + (rank_por_libro - 1) * 0.02
            --           ^ penalización suave por repetir libro
        LIMIT :cantidad
        """
        query = text(f"WITH {top_global}, {ranked} {select_final}")
        # Aumentar probes de ivfflat para mayor precisión
        #    (busca en más clusters del índice, más lento pero más exacto)
        session.execute(text("SET ivfflat.probes = 10"))

        result = session.execute(
            query,
            {
                "pregunta": embedding,
                "cantidad": cantidad_chunks
            }
        ).fetchall()

        # Sin resultados → retora tnupla vacía (compatible con el umbral)
        if not result:
            return []

        chunks = [
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

        #    Extraer la distancia del chunk más cercano.
        #    Este valor es el que se compara contra UMBRAL_DISTANCIA
        #    en response_stream para activar la barrera de protección.

        distancia_minima = min(r.distancia for r in result)

        return chunks, distancia_minima
    except Exception as e:
        print(f"❌ Error en select_chunck: {e}")
        return []

    finally:
        session.close()











