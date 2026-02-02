import json
import openai
from dotenv import load_dotenv
import os
from script.ml.variables_globales import MODELO,CHUNCKS_POR_LIBRO,MODELO_MINI
from script.ml.embeddings.select_chunks import select_chunck
from script.ml.gpt.prompt import prompt_base
from script.controllers.libro import formatear_listado_libros,obtener_listado_libros_con_capitulos
import re
# Cargar clave desde .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Cliente de OpenAI
from openai import OpenAI
client = OpenAI()


def response_stream(pregunta_usuario, historial):
    chunks = select_chunck(pregunta_usuario,historial, CHUNCKS_POR_LIBRO)

    contexto = "\n\n".join([f"Fuente: {c['libro']}\n Fecha: {c['fecha']} \n Autor: {c['autor']} \n Página: {c['pagina']}  \nConocimiento:{c['contenido']}   " for c in chunks])

    print(contexto)
    prompt = prompt_base()

    libros_con_capitulos = obtener_listado_libros_con_capitulos()
    archivos_existentes = formatear_listado_libros(libros_con_capitulos)
    print(archivos_existentes)
    

    if chunks == []:
        mensajes = [
            {
                "role": "system",
                "content": "Responde exactamente: Lo siento, aún no ha cargado información "
            }
        ]
    else:
        

        mensajes = [
            {
                "role": "system",
             "content": (
                prompt
                + "\n\nLISTA DE DOCUMENTOS y capitulos EN BD:\n"
                + "\n".join(archivos_existentes)
                + "\n\nINFORMACIÓN ENCONTRADA:\n"
                + contexto
            )
               }
        ]
    mensajes.extend([
    {
        "role": "user" if msg.rol == "user" else "assistant",
        "content": msg.contenido
    }
    for msg in historial
])


    def event_generator():
        with client.chat.completions.stream(model=MODELO, messages=mensajes) as stream:
            for event in stream:
                if hasattr(event, "delta") and event.delta:
                    yield json.dumps({'contenido': event.delta}) + "\n"
    return event_generator

