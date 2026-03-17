


def formatear_listado_libros(libros_dict):
    """
    Funcion asignada para que el listado 
    de los capitulos se muestren de forma ordenada
    """
    salida = []
    for libro in libros_dict.values():
        salida.append(f"📘 {libro['libro']}")
        salida.append(
             f"Autor: {libro['autor']} | "
            f"Fecha: {libro['fecha']} | "
            f"Tipo: {libro['tipo']}"
        )
        if libro['capitulos']:
            for  cap in libro['capitulos']:
                salida.append(f"- {cap}")
        else:
            salida.append("")  # línea en blanco
    return "\n".join(salida)





import re

def limpiar_titulo(titulo: str) -> str:
    """
    Elimina numeraciones del inicio del título:
    "I. Introducción" → "Introducción"
    "1.1 Conceptos" → "Conceptos"
    "Capítulo 3: Métodos" → "Métodos"
    "3.1. Enfoque" → "Enfoque"
    """
    # Quitar "Capítulo X:", "Capitulo X -", etc.
    titulo = re.sub(r'^cap[ií]tulo\s+[\dIVXivx]+[\s:\-\.]*', '', titulo, flags=re.IGNORECASE)
    # Quitar romanos solos: "I.", "IV.", "VII.   "
    titulo = re.sub(r'^(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.\s*', '', titulo, flags=re.IGNORECASE)
    # Quitar numeración decimal: "3.1.", "3.1.2 ", "1. "
    titulo = re.sub(r'^[\d]+(\.\d+)*[\.\s\-\)]+', '', titulo)
    return titulo.strip()

 

    