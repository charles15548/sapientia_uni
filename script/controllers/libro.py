
from sqlalchemy import text
from fastapi.responses import FileResponse
from fastapi import HTTPException
import os

from script.ml.embeddings.embedding import dividir_en_chunks,limpiar_texto,generar_embedding

from script.bd.db import engine


def subirLibro(nombre_libro, paginas, capitulos,fecha, autor, tipo, tags, url_doc):
    
       

        with engine.begin() as conn:
            resultBook = conn.execute(
                text("""
                    INSERT INTO libros (libro,fecha, autor, tipo, tags, url_doc)
                    VALUES (:libro,:fecha, :autor, :tipo, :tags, :url_doc)
                    RETURNING id;
                """),
                {
                    "libro": nombre_libro,
                    "fecha": fecha,
                    "autor": autor,
                    "tipo": tipo,
                    "tags": tags,
                    "url_doc": url_doc
                }
            )
            bookId = resultBook.scalar()

            if capitulos:
                conn.execute(
                    text("""
                        INSERT INTO capitulos (id_libro, titulo)
                        VALUES (:id_libro, :titulo)

                    """),
                    [
                        {
                        "id_libro": bookId,
                        "titulo": c["titulo"]
                        }
                        for c in capitulos
                    ]
                )


        TAMAÑO_LOTE = 40

        lote = []
        total_chunks = 0

        for pagina in paginas:
            num_pag = pagina["pagina"]
            texto = pagina["texto"]
            print(f"📄 Procesando página {num_pag}")

            for chunk in dividir_en_chunks(
                 texto
            ):
                chunk_limpio = limpiar_texto(chunk)
                if not chunk_limpio:
                      continue
                embedding = generar_embedding(chunk_limpio)
                if embedding is None:
                    continue

                #emb = np.array(embedding, dtype=np.float32)

                lote.append({
                    "id_libro": bookId,
                    "contenido": chunk_limpio,
                    "embedding": embedding.tolist(),
                    "pagina": num_pag
                })
                total_chunks +=1

                if len(lote) >= TAMAÑO_LOTE:
                    _insertar_lote_embeddings(lote)
                    print(f"💾 Insertados {total_chunks} chunks")
                    lote.clear()
        # 🔹 3. Último remanente
        if lote:
            _insertar_lote_embeddings(lote)
            print(f"💾 Insertados {total_chunks} chunks (final)")

        print("✅ Documento procesado completamente")
        return bookId









    
def _insertar_lote_embeddings(lote):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO document_chunks
                    (id_libro, contenido, embedding, pagina)
                VALUES
                    (:id_libro, :contenido, (:embedding)::vector, :pagina)
            """),
            lote
        )


            
            
def listar_libros():
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                SELECT id, libro, fecha, autor, tipo, tags
                FROM libros
                ORDER BY id DESC
            """)
        ).fetchall()

    return [
        {
            "id": r.id,
            "nombre_libro": r.libro,
            "fecha": r.fecha,
            "autor": r.autor,
            "tipo": r.tipo,
            "tags": r.tags
        }
        for r in result
    ]



def eliminar_libro(id_libro: int) -> bool:
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                DELETE FROM libros
                WHERE id = :id_libro
            """),
            {"id_libro": id_libro}
        )

    return result.rowcount > 0



def obtener_listado_libros_con_capitulos():
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        l.id,
                        l.libro,
                        l.fecha,
                        l.autor,
                        l.tipo,
                        l.tags,
                        c.titulo AS capitulo
                    FROM libros l
                    LEFT JOIN capitulos c ON c.id_libro = l.id
                    ORDER BY l.id
                """)
            ).fetchall()

        libros = {}
        for r in result:
            if r.id not in libros:
                libros[r.id] = {
                    "libro": r.libro,
                    "autor": r.autor,
                    "fecha": r.fecha,
                    "tipo": r.tipo,
                    "tags": r.tags,
                    "capitulos": []
                }
            if r.capitulo:
                libros[r.id]["capitulos"].append(r.capitulo)

        return libros

    except Exception as e:
        print(f"❌ Error listado libros-capítulos: {e}")
        return {}




def formatear_listado_libros(libros_dict):
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



def descargar_libro_por_id(id_libro: int):
    with engine.begin() as conn:
        libro = conn.execute(
            text("""
                SELECT libro, url_doc
                FROM libros
                WHERE id = :id
            """),
            {"id": id_libro}
        ).fetchone()
    if not libro:
        raise HTTPException(404, "Libro no encontrado")

    if not libro.url_doc or not os.path.exists(libro.url_doc):
        raise HTTPException(404, "Archivo no disponible")

    return FileResponse(
        path=libro.url_doc,
        filename=os.path.basename(libro.url_doc),
        media_type="application/octet-stream"
    )