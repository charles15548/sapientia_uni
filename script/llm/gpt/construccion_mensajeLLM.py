from script.llm.gpt.prompt import PROMPT_BASE, PROMPT_GUARDRAIL
from script.controllers.capitulos import obtener_listado_libros_con_capitulos
from script.service.libroCapitulosService import formatear_listado_libros


def construir_mensajes_rechazo(pregunta_usuario):
    return [
        {
            "role": "system",
            "content": PROMPT_GUARDRAIL
        },
        {
            "role": "user",
            "content": pregunta_usuario
        }
    ]


def construir_mensajes_principal(chunks, historial):
    contexto = "\n\n".join([
        f"Fuente: {c['libro']}\n"
        f"Fecha: {c['fecha']}\n"
        f"Autor: {c['autor']}\n"
        f"Página: {c['pagina']}\n"
        f"Conocimiento: {c['contenido']}"
        for c in chunks
    ])
    print(contexto)

    print(" ".join(contexto.split()[:200]) + "...")
    libros_con_capitulos = obtener_listado_libros_con_capitulos()
    archivos_existentes = formatear_listado_libros(libros_con_capitulos)
    mensajes = [
        {
            "role": "system",
            "content": (
                PROMPT_BASE
                + "\n\nLISTA DE DOCUMENTOS EN BD:\n"
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

    return mensajes