from backend.config.firebase_config import db
from datetime import datetime

def registrar_admin(nombre,matricula, correo):

    admin = {
        "nombre": nombre,
        "matricula": matricula,
        "correo": correo,
        "rol": "admin",
        "fecha_registro": datetime.now()
    }

    db.collection("administradores").add(admin)

    print("Administrador registrado")