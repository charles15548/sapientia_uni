import os
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
import re
from script.ml.variables_globales import CHUNK_LIBRO, OVERLAP




load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_embedding(texto: str) -> np.ndarray | None:
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        return np.array(response.data[0].embedding, dtype="float32")
    except Exception as e:
        print(f"❌ Error generando embedding: {e}")
        return None


def limpiar_texto(texto: str) -> str:
    return re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]','',texto)

def dividir_en_chunks(texto: str, max_palabras: int = CHUNK_LIBRO, overlap: int = OVERLAP) -> list[str]:
    texto = re.sub(r"\s+", " ", texto).strip()

    palabras = texto.split(" ")
    chunks = []

    inicio = 0
    while inicio < len(palabras):
        fin = inicio + max_palabras
        chunk = palabras[inicio:fin]
        chunks.append(" ".join(chunk))
        inicio = fin - overlap

    return chunks
