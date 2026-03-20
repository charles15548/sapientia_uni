import fitz
from script.llm.embeddings.libros.formatear_libro import  contar_texto, limpiar_texto_estructural
from script.llm.variables_globales import MIN_TEXTO_POR_PAGINA
from docx import Document
from fastapi import HTTPException

def extraer_paginas_pdf(archivo) -> list:
    # Leer archivo
    contenido = archivo.file.read()
    archivo.file.seek(0)
    doc = fitz.open(stream=contenido,filetype="pdf")
    paginas = []

    for page in doc:
        # Obtener texto
        texto = page.get_text(sort=True)
        # Limpiar Texto por pagina
        texto_limpio = limpiar_texto_estructural(texto)

        if not texto_limpio:
            continue
        # Dejar pasar las paginas que tienen contenido valido
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
        # Utilizado para el word
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