from backend.config.firebase_config import db
from datetime import datetime


def registrar_acceso(nombre,matricula, estado, foto_url=None):
    try:
        # 🔥 CONVERTIR A URL COMPLETA SI EXISTE
        if foto_url and not foto_url.startswith("http"):
            foto_url = f"https://bioaccessapis.onrender.com/{foto_url}"
        data = {
            "nombre": nombre,
            "estado": estado,
            "matricula": matricula,
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M:%S"),
            "foto": foto_url,
            "timestamp": datetime.now()
        }

        # Agregamos un print para ver en la terminal que se está intentando guardar
        print(f"Enviando a Firebase: {nombre} ({estado})")
        
        db.collection("accesos").add(data)
        
        print(f"Guardado exitoso para: {nombre}")
        return True
    except Exception as e:
        print(f"Error al guardar en Firebase: {e}")
        return False
