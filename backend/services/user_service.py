from backend.config.firebase_config import db
from datetime import datetime


def registrar_usuario(nombre,matricula, rol="estudiante"):

    usuario = {
        "nombre": nombre,
        "matricula": matricula,
        "rol": rol,
        "fecha_registro": datetime.now()
    }

    db.collection("usuarios").add(usuario)

    print(f"Usuario {nombre} registrado en la base de datos")