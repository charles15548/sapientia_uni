from pypdf import PdfReader
from io import BytesIO
from fastapi import UploadFile
from script.controllers.libro import subirLibro
from script.controllers.libro import formatear_listado_libros
from docx import Document
import shutil
import os
import fitz
import re
from fastapi import HTTPException
from script.ml.variables_globales import MIN_TEXTO_POR_PAGINA,MODELO_CAPITULO,RUTA_BASE
from script.ml.gpt.prompt import PROMPT_CAPITULOS

 
def limpiar_texto_rag(texto: str) -> str:
    # Eliminar NUL explícitamente (CRÍTICO)
    texto = texto.replace("\x00", "")

    # Normalizar saltos raros
    texto = texto.replace("\r", "\n")

    # Eliminar caracteres de control (excepto \n y \t)
    texto = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", texto)

    # Colapsar espacios excesivos
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()

def contar_texto(texto: str) -> int:
    if not texto:
        return 0
    return len(texto.strip())

def limpiar_texto_estructural(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.replace("\x00", "")
    texto = texto.replace("\r", "\n")
    return texto




def extraer_paginas_pdf(archivo) -> list:
    contenido = archivo.file.read()
    archivo.file.seek(0)
    doc = fitz.open(stream=contenido,filetype="pdf")
    paginas = []

    for page in doc:
        texto = page.get_text(sort=True)
        texto_limpio = limpiar_texto_estructural(texto)

        if not texto_limpio:
            continue
        if contar_texto(texto_limpio) < MIN_TEXTO_POR_PAGINA:
            continue

        paginas.append({
                "pagina": page.number +1,
                "texto": texto_limpio
        })
    print(f"📘 PÁGINAS ÚTILES: {len(paginas)} / {len(doc)}")
    return paginas


def extraer_paginas_word(archivo) -> list:
    try:
        doc = Document(archivo.file)
    except Exception:
        raise HTTPException(status_code=400, detail="Word corrupto")
    
    paginas =[]
    texto_actual = []

    for p in doc.paragraphs:
        if p.text.strip():
            texto_actual.append(p.text.strip())
    texto_final = "\n".join(texto_actual)

    if contar_texto(texto_final) < MIN_TEXTO_POR_PAGINA:
        return []
    paginas.append({
        "pagina":1,
        "texto": texto_final
    })
    archivo.file.seek(0)
    return paginas

import openai
from dotenv import load_dotenv
import json
from openai import OpenAI

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def detectar_capitulos(paginas):
    if not paginas:
        return []
    
    paginas_recortadas = paginas[:30]

    prompt = PROMPT_CAPITULOS


    response = client.chat.completions.create(
        model=MODELO_CAPITULO, 
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": json.dumps({"paginas": paginas_recortadas}, ensure_ascii=False)
            }
        ]
    )

    contenido = response.choices[0].message.content

    try:
        data = json.loads(contenido)
        return data.get("capitulos", [])
    except json.JSONDecodeError:
        print("❌ Error parseando JSON de capítulos")
        return []

 

def guardar_libro_en_disk(
        nombre_libro: str,
        archivo: UploadFile,
        extension: str
) -> str:
    try:
        os.makedirs(RUTA_BASE, exist_ok=True)
        nombre_limpio = nombre_libro.replace(" ", "_")


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
        
        texto_total = " ".join(p["texto"] for p in paginas)
        if contar_texto(texto_total) < 200:

            raise HTTPException(
                status_code=400,
                detail="No se pudo leer el libro. Parece que no contiene texto legible."
            )

        capitulos = detectar_capitulos(paginas)
        print("📚 Capítulos detectados:")
         

        print(f"""
            ==========
            {capitulos}
            ==========""")

        for p in paginas:
            p["texto_rag"] = limpiar_texto_rag(p["texto"])



        subirLibro(
            nombreLibro,
            paginas,
            capitulos,fecha, autor, tipo, tags,
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


