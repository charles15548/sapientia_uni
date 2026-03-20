import json
import openai
from dotenv import load_dotenv
import os
from script.llm.variables_globales import MODELO,CHUNCKS_POR_LIBRO, UMBRAL_DISTANCIA
from script.llm.embeddings.select_chunks import select_chunck
from script.llm.gpt.construccion_mensajeLLM import construir_mensajes_rechazo, construir_mensajes_principal

# Cargar clave desde .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Cliente de OpenAI
from openai import OpenAI
client = OpenAI()


def response_stream(pregunta_usuario, historial):
    chunks,distancia_minima = select_chunck(pregunta_usuario,historial, CHUNCKS_POR_LIBRO)

    # --------------------------------------------------------
    # BARRERA DE PROTECCIÓN DE DOMINIO
    # Se activa si cualquiera de estas condiciones es verdadera:
    #   - No se encontró ningún chunk
    #   - La distancia no pudo calcularse
    #   - El chunk más cercano supera el umbral (fuera de dominio)
    # --------------------------------------------------------
    sin_contexto = (
        not chunks or   
        distancia_minima is None or
        distancia_minima > UMBRAL_DISTANCIA
    )
    print(f"Distancia mínima: {distancia_minima} | Sin contexto: {sin_contexto}")
    
    mensajes = (
        # --------------------------------------------------------
        # RAMAL DE RECHAZO
        # LLM liviano, sin chunks, sin lista de libros.
        # Solo recibe la pregunta y una instrucción breve.
        # Objetivo: respuesta amable que no invente nada.
        # --------------------------------------------------------
        
        construir_mensajes_rechazo(pregunta_usuario)
        if sin_contexto else
        
        construir_mensajes_principal(chunks,historial)
        # --------------------------------------------------------
        # RAMAL PRINCIPAL
        # Flujo completo: contexto de chunks + lista de libros
        # + historial conversacional + prompt base.
        # --------------------------------------------------------

    )


    def event_generator():
        with client.chat.completions.stream(model=MODELO, messages=mensajes) as stream:
            for event in stream:
                if hasattr(event, "delta") and event.delta:
                    yield json.dumps({'contenido': event.delta}) + "\n"
    return event_generator

