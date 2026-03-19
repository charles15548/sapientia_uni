from script.controllers.personas import login

from fastapi import FastAPI, HTTPException,Form,File,Body,UploadFile
from fastapi.responses import JSONResponse
from script.ml.embeddings.libros.subir_libro import procesarSubida, guardar_libro_en_disk
from script.controllers.libro import eliminar_libro, listar_libros,descargar_libro_por_id
from script.controllers.capitulos import obtener_listado_libros_con_capitulos_service
from script.controllers.capitulos import editar_capitulo,editar_subcapitulo, crear_capitulo, eliminar_capitulo, crear_subcapitulo,eliminar_subcapitulo
from script.ml.response import response_stream
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List,Literal
from pydantic import BaseModel
import json
import logging



from fastapi.responses import StreamingResponse

from dotenv import load_dotenv
load_dotenv()
app = FastAPI(title="API RAG")

origins = [
    "http://localhost:3000",              
    "https://soporte2.intelectiasac.com", 
    "https://ipp.intelectiasac.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Mensaje(BaseModel):
    rol: Literal["user","bot"]
    contenido: str

class PreguntaEntrada(BaseModel):
    pregunta: str
    historial: List[Mensaje]



@app.post("/consultar-stream")
def consultar_stream(pregunta_entrada: PreguntaEntrada):
    try:
        
        pregunta = pregunta_entrada.pregunta
        historial = pregunta_entrada.historial

        response = response_stream(pregunta,historial)

        return StreamingResponse(response(), media_type="text/event-stream")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))







@app.post("/acceso")
async def log(
correo: str = Form(...),
contrasena: str = Form(...),
):
    logging.warning("login ejecutado")
    
    
    user = login(correo,contrasena)
    return user


    

@app.get("/libros")
def obtener_libros():
    try:
        libros = listar_libros()
        return {
            "total": len(libros),
            "libros": libros
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Error al obtener la lista de libros"
        )


@app.get("/libros/con-capitulos")
def obtener_libros_y_capitulos():
    try:
        libros = obtener_listado_libros_con_capitulos_service()
        return {
            "total": len(libros),
            "libros": libros
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Error al obtener la lista de libros"
        )
  


@app.get("/libros/{id}/descargar")
def descargar(id: int):
    return descargar_libro_por_id(id)

@app.post("/subir-libro")
async def subir_documento(
    nombreLibro:str = Form(...),
    contenido: UploadFile=File(...),
    fecha: str = Form(...),
    autor: str = Form(...),
    tipo: str = Form(...),
    tags: str = Form(...),

):
    try:
        return procesarSubida(nombreLibro, contenido, fecha, autor, tipo, tags)

    except HTTPException as e:
        raise e
        
       
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Error al insertar el libro ❌"
        )

# @app.post("/subir-libro")
# async def subir_documento_striming(
#     nombreLibro: str = Form(...),
#     contenido: UploadFile = File(...)
# ):

#     async def event_stream():
#         try:
#             yield json.dumps({"tipo": "info", "mensaje": "📘 Iniciando carga del libro"}) + "\n"

#             for evento in procesarSubida(nombreLibro, contenido):
#                 yield json.dumps(evento) + "\n"

#             yield json.dumps({"tipo": "done", "mensaje": "✅ Libro insertado correctamente"}) + "\n"

#         except Exception as e:
#             yield json.dumps({"tipo": "error", "mensaje": str(e)}) + "\n"

#     return StreamingResponse(event_stream(), media_type="text/plain")













@app.delete("/libros/{id_libro}")
def borrar_libro(id_libro: int):
    try:
        eliminado = eliminar_libro(id_libro)

        if not eliminado:
            raise HTTPException(
                status_code=404,
                detail="Libro no encontrado"
            )

        return {
            "message": f"Libro con id {id_libro} eliminado correctamente ✅"
        }

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar el libro"
        )


import os
import time
@app.post("/disk/subir-manual")
async def subir_manual(
    nombreLibro: str = Form(...),
    archivo: UploadFile = File(...)
):
    try:
        extension = os.path.splitext(archivo.filename)[1]

        if extension not in [".pdf", ".docx"]:
            raise HTTPException(status_code=400, detail="Formato no permitido")

        # evitar sobrescribir
        nombre_final = f"{nombreLibro}_{int(time.time())}"

        ruta = guardar_libro_en_disk(
            nombre_final,
            archivo,
            extension
        )

        return {
            "ok": True,
            "ruta": ruta
        }

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Error al subir archivo al disk"
        )






# ===============
# CAPITULOS
# ===============


@app.post("/libros/{id_libro}/capitulos")
def endpoint_crear_capitulo(id_libro: int, body: dict):
    try:
        titulo = body.get("titulo", "").strip()
        if not titulo:
            raise HTTPException(status_code=400, detail="El título no puede estar vacío")
        return crear_capitulo(id_libro, titulo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al crear capítulo")

@app.put("/capitulos/{cap_id}")
def endpoint_editar_capitulo(cap_id: int, body: dict):
    try:
        nuevo_titulo = body.get("titulo","").strip()
        if not nuevo_titulo:
            raise HTTPException(status_code=400, detail="El título no puede estar vacío")
        return editar_capitulo(cap_id, nuevo_titulo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al editar capítulo")


@app.delete("/capitulos/{cap_id}")
def endpoint_eliminar_capitulo(cap_id: int):
    try:
        return eliminar_capitulo(cap_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al eliminar capítulo")





# ===============
# SUB CAPITULOS
# ===============
@app.post("/capitulos/{id_capitulo}/subcapitulos")
def endpoint_crear_subcapitulo(id_capitulo: int, body: dict):
    try:
        titulo = body.get("titulo", "").strip()
        if not titulo:
            raise HTTPException(status_code=400, detail="El título no puede estar vacío")
        return crear_subcapitulo(id_capitulo, titulo)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear subcapítulo")



@app.put("/subcapitulos/{sub_id}")
def endpoint_editar_subcapitulo(sub_id: int, body: dict):
    try:
        nuevo_titulo = body.get("titulo","").strip()
        if not nuevo_titulo:
            raise HTTPException(status_code=400, detail="El título no puede estar vacío")
        return editar_subcapitulo(sub_id, nuevo_titulo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al editar capítulo")

@app.delete("/subcapitulos/{sub_id}")
def endpoint_eliminar_subcapitulo(sub_id: int):
    try:
        return eliminar_subcapitulo(sub_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error al eliminar subcapítulo")





# Ejecutar: uvicorn app:app --reload
if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8001, reload=False)