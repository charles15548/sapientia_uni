from pypdf import PdfReader
from io import BytesIO
from fastapi import UploadFile
from script.controllers.libro import subirLibro
from script.llm.embeddings.libros.formatear_libro import limpiar_texto_rag, contar_texto
from script.llm.embeddings.libros.subir_capitulos import detectar_capitulos
from script.llm.embeddings.libros.extraer_paginas import extraer_paginas_pdf,extraer_paginas_word
import shutil
import os

 
from fastapi import HTTPException
from script.llm.variables_globales import RUTA_BASE

import openai
from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()



 

def guardar_libro_en_disk(
        nombre_libro: str,
        archivo: UploadFile,
        extension: str
) -> str:
    """
    Guarda el libro en el storage de Render puede ser PDF O WORD,
    esto se usara para la funcion descargar libro
    """
    try:
        
        os.makedirs(RUTA_BASE, exist_ok=True)
        nombre_limpio = nombre_libro.replace(" ", "_")

        # Limpiamos la ruta para evitar errores al guardar por el nombre
        ruta_final = os.path.join(
            RUTA_BASE,
            f"{nombre_limpio}{extension}"
        )

        with open(ruta_final, "wb") as buffer:
            shutil.copyfileobj(archivo.file,buffer)
        archivo.file.seek(0)

        return ruta_final



    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Error al guardar el libro en el disk ❌"
        )


def procesarSubida(nombreLibro, contenido,fecha, autor, tipo, tags):


    extension = os.path.splitext(contenido.filename)[1]
    url_doc = None

    try:
        # Se guarda el libro como tal, ej: pdf
        # para poder descargarlo y revisarlo posteriormente 
        url_doc = guardar_libro_en_disk(
            nombreLibro, contenido,extension
        )
        print(f"Libro guardado en: {url_doc}")

        


        if extension == ".pdf":
            paginas = extraer_paginas_pdf(contenido)
        elif extension == ".docx":
            paginas = extraer_paginas_word(contenido)
        else:
            raise HTTPException(status_code=400, detail="Formato no soportado")
        
        # Controlar que no se suba libros vacios
        texto_total = " ".join(p["texto"] for p in paginas)
        if contar_texto(texto_total) < 200:

            raise HTTPException(
                status_code=400,
                detail="No se pudo leer el libro. Parece que no contiene texto legible."
            )
        # Detectar los capitulos con IA
        capitulos = detectar_capitulos(paginas)
        
        # Limpieza de textos corruptos que puedan dañar los chunks
        for p in paginas:
            p["texto_rag"] = limpiar_texto_rag(p["texto"])



        subirLibro(
            nombreLibro,
            paginas,
            capitulos,
            fecha, 
            autor, 
            tipo, 
            tags,
            url_doc
        )
        return {"message": f"Libro {nombreLibro} insertado correctamente ✅"}
    except Exception as e:
        if url_doc and os.path.exists(url_doc):
            os.remove(url_doc)
            print("Archivo eliminado correctamente")
        print(e)
        if isinstance(e, HTTPException):
            raise e

        raise HTTPException(
            status_code=500,
            detail="Error al procesar la subida del libro ❌"
        )


