import re
from script.llm.variables_globales import MODELO_MINI




def limpiar_texto_rag(texto: str) -> str:
    """
    Esta función sera usada para limpiar 
    el texto extraido de los pdfs, de tal forma
    que no exista errores al subir
    """
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
    """
    Función util para controlar que cada pagina
    tenga un minimo de textos subidos,
    evitando tener embeddings vacios ocupando espacio
    de almacenamiento
    """
    if not texto:
        return 0
    return len(texto.strip())


def limpiar_texto_estructural(texto: str) -> str:
    """
    Limpia de forma menos riesgosa para extraer paginas PDF,
    este es el primer filtro, por lo que solo es una limpieza minima
    """
    if not texto:
        return ""
    texto = texto.replace("\x00", "")
    texto = texto.replace("\r", "\n")
    return texto