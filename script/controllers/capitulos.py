from sqlalchemy import text
from script.bd.db import engine
from fastapi import   HTTPException

def obtener_listado_libros_con_capitulos_service():
     
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
                        c.id     AS capitulo_id,
                        c.titulo AS capitulo,
                        c.orden  AS capitulo_orden,
                        s.id     AS sub_id,
                        s.titulo AS subcapitulo,
                        s.orden  AS sub_orden
                    FROM libros l
                    LEFT JOIN capitulos c ON c.id_libro = l.id
                    LEFT JOIN subcapitulos s ON s.id_capitulo = c.id
                    ORDER BY l.id, c.orden, s.orden
                """)
            ).fetchall()

        libros = {}
        for r in result:
            if r.id not in libros:
                libros[r.id] = {
                    "id": r.id,
                    "nombre_libro": r.libro,
                    "autor": r.autor,
                    "fecha": r.fecha,
                    "tipo": r.tipo,
                    "tags": r.tags,
                    "capitulos": {}
                }
            if r.capitulo_id and r.capitulo_id not in libros[r.id]["capitulos"]:
                libros[r.id]["capitulos"][r.capitulo_id] = {
                    "id": r.capitulo_id,
                    "capitulo": r.capitulo,
                    "subcapitulos": []
                }
            if r.sub_id:
                libros[r.id]["capitulos"][r.capitulo_id]["subcapitulos"].append(
            {
                "id": r.sub_id,
                "titulo": r.subcapitulo
            }
                )

        for libro in libros.values():
            libro["capitulos"] = list(libro["capitulos"].values())

        return list(libros.values())

    except Exception as e:
        print(f"❌ Error listado libros-capítulos: {e}")
        import traceback
        traceback.print_exc()
        return []

  
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
    


def editar_capitulo(cap_id, nuevo_titulo):
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                UPDATE capitulos
                SET titulo = :titulo
                WHERE id = :id
                RETURNING id, titulo
            """),
            {"id":cap_id,"titulo": nuevo_titulo.strip()}
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Capítulo no encontrado")
    return {"id": row.id, "titulo": row.titulo}

def editar_subcapitulo(sub_id, nuevo_titulo):
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                    UPDATE subcapitulos
                    SET titulo = :titulo
                    WHERE id = :id
                    RETURNING id, titulo            
            """),
            {"id": sub_id, "titulo": nuevo_titulo.strip()}            
        )

        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Subcapítulo no encontrado")
        return {"id": row.id, "titulo": row.titulo}