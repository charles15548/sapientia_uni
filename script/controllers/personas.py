from sqlalchemy import  text

import jwt,datetime
from script.bd.db import engine



SECRET_KEY = "clave101"
ALGORITHM = "HS256"


def agregarPersona(nombre , apellidos, correo , contrasena , foto  ):
    with engine.connect() as conn:
        query = text("""
            INSERT INTO persona (nombre, apellidos, correo, contrasena, foto)
            VALUES (:nombre, :apellidos, :correo, :contrasena, :foto)
            RETURNING id;
        """)
        result = conn.execute(query,{
            "nombre": nombre,
            "apellidos": apellidos,
            "correo": correo,
            "contrasena": contrasena,
            "foto":foto
        })
        persona_id = result.scalar()
        print(f"Persona agregada con id {persona_id}")
        conn.commit()
        return persona_id

def login(correo, contrasena):
    with engine.connect() as conn:
        query = text("""
            SELECT id,contrasena,correo FROM persona
            WHERE correo = :correo
            LIMIT 1;
        """)
        result = conn.execute(query, {'correo':correo})

        user = result.fetchone()
        if user:
            if user.contrasena == contrasena:
                exp = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
                token = jwt.encode(
                    {"id": user.id, "correo": user.correo, "exp":exp},
                    SECRET_KEY,
                    algorithm=ALGORITHM
                )
                return {"id": user.id,"token":token, "message": "Ingresando"}
            else:
                    return {"id":0, "message":"Contraseña incorrecta"}
            
        else:
            return {"id": 0, "message":"No se encontro usuario"}


# if __name__ == "__main__":
#     agregarPersona(
#     nombre="usuario",
#     apellidos="usuario",
#     correo="usuario@gmail.com",
#     contrasena="usuario",
#     foto=""
#     )