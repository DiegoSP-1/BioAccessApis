from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.config.firebase_config import db
from backend.services.access_service import registrar_acceso 
from backend.services.camera_check import autodiagnostico_camara
from backend.services.email_services import enviar_otp_email
import base64
import os
import time
import random
import cv2
import numpy as np
import json
import subprocess
import sys
from datetime import datetime

app = FastAPI()

# ===============================
# CONFIGURACIÓN DE RUTAS 
# ===============================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Crear carpetas en la raíz
for carpeta in ["capturas", "dataset", "registro", "otp", "dashboard", "scan", "model"]:
    ruta_folder = os.path.join(BASE_DIR, carpeta)
    if not os.path.exists(ruta_folder):
        os.makedirs(ruta_folder)

# RUTAS ABSOLUTAS PARA EL MODELO
modelo_path = os.path.join(BASE_DIR, "model", "modelo.yml")
labels_path = os.path.join(BASE_DIR, "model", "labels.json")

recognizer = cv2.face.LBPHFaceRecognizer_create()
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

if os.path.exists(modelo_path):
    recognizer.read(modelo_path)
    with open(labels_path, "r") as f:
        labels = {int(k): v for k, v in json.load(f).items()}
    print(f"Motor Biométrico cargado desde: {modelo_path}")
else:
    print("ADVERTENCIA: No se encontró modelo.yml en la carpeta model/")

ultimo_acceso_web = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def home():
    return {"mensaje": "API BioAccess funcionando correctamente"}

# ===============================
# ENDPOINT DE PRUEBA
# ===============================
@app.get("/")
def home():
    return {"mensaje": "API BioAccess funcionando correctamente"}

@app.post("/registro")
def registrar_usuario(data: dict):
    try:
        nombre = data.get("nombre").strip()
        matricula = data.get("matricula")
        correo = data.get("correo")
        fotos = data.get("fotos")

        # Ruta absoluta en la raíz del proyecto
        carpeta = os.path.join(BASE_DIR, "dataset", nombre)
        
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

        for i, foto in enumerate(fotos):
            try:
                if "," in foto:
                    img_data = foto.split(",")[1]  # FIX
                else:
                    img_data = foto

                img_bytes = base64.b64decode(img_data)
                ruta_foto = os.path.join(carpeta, f"{i}.jpg")
                
                with open(ruta_foto, "wb") as f:
                    f.write(img_bytes)

            except Exception:
                # Ignora errores individuales de fotos
                pass

        # Guardado en Firebase
        db.collection("usuarios").add({
            "nombre": nombre,
            "matricula": matricula,
            "correo": correo,
            "fecha_registro": time.strftime("%Y-%m-%d")
        })

        return {"mensaje": "Usuario registrado correctamente"}

    except Exception as e:
        return {"error": str(e)}

# ===============================
# OBTENER ACCESOS
# ===============================
@app.get("/accesos")
def obtener_accesos():
    try:
        docs = db.collection("accesos").limit(50)

        lista = []
        for doc in docs:
            data = doc.to_dict()

            lista.append({
                "nombre": data.get("nombre", "N/A"),
                "matricula": data.get("matricula", "N/A"),
                "fecha": data.get("fecha", "N/A"),
                "hora": data.get("hora", "N/A"),
                "estado": data.get("estado", "N/A"),
                "foto": data.get("foto", None)
            })

            lista_ordenada = sorted(
                lista,
                key = lambda x: f"{x.get('fecha',")}{x.get('hora',")}",
                reverse=True
            )

        return lista_ordenada[:15]

    except Exception as e:
        return {"error": "Error al obtener accesos", "detalle": str(e)}

# almacenamiento temporal de OTPs
otp_storage = {}

# ===============================
# GENERAR OTP
# ===============================
@app.post("/generar-otp")
def generar_otp(data: dict):
    matricula = data.get("matricula")

    docs = db.collection("usuarios").where("matricula", "==", matricula).stream()

    usuario = None
    for doc in docs:
        usuario = doc.to_dict()

    if not usuario:
        return {"error": "Usuario no encontrado"}
    
    correo = usuario.get("correo")

    if not correo:
        return {"error": "El usuario no tiene correo registrado"}

    otp = str(random.randint(100000, 999999))

    otp_storage[matricula] = {
        "otp": otp,
        "expira": time.time() + 300
    }

    enviar_otp_email(correo, otp)

    print(f"OTP para {matricula}: {otp}")

    return {"mensaje": "OTP enviado"}

# ===============================
# VALIDAR OTP
# ===============================
@app.post("/validar-otp")
def validar_otp(data: dict):
    matricula = data.get("matricula")
    otp_ingresado = data.get("otp")

    if matricula not in otp_storage:
        return {"error": "OTP no encontrado"}

    otp_data = otp_storage[matricula]

    if time.time() > otp_data["expira"]:
        return {"error": "OTP expirado"}

    if otp_ingresado != otp_data["otp"]:
        return {"error": "OTP incorrecto"}

    return {"mensaje": "Acceso permitido"}

# ===============================
# ESTADÍSTICAS
# ===============================
@app.get("/estadisticas")
def estadisticas():
    try:
        docs = db.collection("accesos").stream()

        total = 0
        permitidos = 0
        denegados = 0
        horas = [0] * 24

        for doc in docs:
            data = doc.to_dict()

            total += 1

            if data.get("estado") == "Permitido":
                permitidos += 1
            else:
                denegados += 1

            hora_str = data.get("hora", "00:00:00")

            try:
                hora = int(hora_str.split(":")[0])
                if 0 <= hora < 24:
                    horas[hora] += 1
            except:
                pass

        return {
            "total": total,
            "permitidos": permitidos,
            "denegados": denegados,
            "horas": horas
        }

    except Exception as e:
        return {"error": "Error al generar estadísticas", "detalle": str(e)}

# ===============================
# OBTENER USUARIOS
# ===============================
@app.get("/usuarios")
def obtener_usuarios():
    try:
        docs = db.collection("usuarios").stream()

        usuarios = []
        for doc in docs:
            data = doc.to_dict()

            usuarios.append({
                "nombre": data.get("nombre", "N/A"),
                "rol": data.get("rol", "N/A"),
                "fecha_registro": str(data.get("fecha_registro", "N/A"))
            })

        return usuarios

    except Exception as e:
        return {"error": "Error al obtener usuarios", "detalle": str(e)}

# ===============================
# ALERTAS (DESCONOCIDOS)
# ===============================
@app.get("/alertas")
def obtener_alertas():
    try:
        docs = db.collection("accesos").stream()

        alertas = []
        for doc in docs:
            data = doc.to_dict()

            if data.get("estado") == "Denegado":
                alertas.append({
                    "nombre": data.get("nombre"),
                    "fecha": data.get("fecha"),
                    "hora": data.get("hora"),
                    "foto": data.get("foto", None)
                })

        return alertas

    except Exception as e:
        return {"error": "Error al obtener alertas", "detalle": str(e)}

# ===============================
# REGISTRAR VISITANTE (OTP)
# ===============================
@app.post("/registrar-visitante")
def registrar_visitante(data: dict):
    try:
        nombre = data.get("nombre")
        motivo = data.get("motivo", "Sin motivo")
        foto_b64 = data.get("foto") 

        if not nombre:
            return {"error": "El nombre es obligatorio"}

        foto_nombre = None

        if foto_b64:
            try:
                header, encoded = foto_b64.split(",", 1)
                img_bytes = base64.b64decode(encoded)

                foto_nombre = f"visitante_{int(time.time())}.jpg"
                foto_path = os.path.join(BASE_DIR, "capturas", foto_nombre)

                with open(foto_path, "wb") as f:
                    f.write(img_bytes)

            except Exception as e:
                print("Error guardando foto:", e)
                foto_nombre = None
        db.collection("visitantes").add({
            "nombre": nombre,
            "motivo": motivo,
            "fecha": time.strftime("%Y-%m-%d"),
            "hora": time.strftime("%H:%M:%S"),
            "timestamp": datetime.now(),
            "foto": foto_nombre
        })

        return {"mensaje": "Registro exitoso"}

    except Exception as e:
        return {"error": str(e)}


# ===============================
# OBTENER VISITANTES (DASHBOARD)
# ===============================
@app.get("/visitantes")
def obtener_visitantes():
    try:
        docs = db.collection("visitantes").limit(50).stream()

        lista = [doc.to_dict() for doc in docs]

        lista_ordenada = sorted(
            lista,
            key=lambda x: x.get("fecha", ""),
            reverse=True
        )

        return lista_ordenada[:10]

    except Exception as e:
        return {"error": str(e)}

"""
@app.post("/activar-escaneo")
def activar_reconocimiento(data: dict = None): # Agregamos '= None' para que no sea obligatorio
    try:
        ruta_script = os.path.join(os.getcwd(), "main.py")
        if not os.path.exists(ruta_script):
            return {"error": "El motor local no existe."}
        
        # OJO: Solo úsalo si el navegador TIENE LA CÁMARA APAGADA
        subprocess.Popen([sys.executable, ruta_script])
        
        return {"mensaje": "Motor local iniciado."}
    except Exception as e:
        return {"error": str(e)}"""
    
# ===============================
# PROCESAR FRAME (MODO WEB)
# ===============================
@app.post("/procesar-frame")
async def procesar_frame(data: dict):
    
    try:       
        foto_b64 = data.get("foto")
        if not foto_b64: return {"error": "No llegó la foto"}

        header, encoded = foto_b64.split(",", 1)
        nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        errores = autodiagnostico_camara(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return {"status": "Buscando...", "diagnostico": errores}

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            label, confidence = recognizer.predict(face)
            ahora = time.time()

            print(f"👤 Rostro: Etiqueta {label} | Confianza {confidence}")

            if confidence < 80:
                nombre = labels[label]
                if nombre not in ultimo_acceso_web or ahora - ultimo_acceso_web[nombre] > .5:
                    docs = db.collection("usuarios").where("nombre", "==", nombre).stream()
                    matricula = "N/A"
                    for doc in docs:
                        user = doc.to_dict()
                        matricula = user.get("matricula", "N/A")
                        foto_nombre = f"ok_{int(ahora)}.jpg"
                        foto_path = os.path.join(BASE_DIR, "capturas", foto_nombre)
                        cv2.imwrite(foto_path, frame)
                    registrar_acceso(nombre ,matricula ,"Permitido", foto_nombre)
                    ultimo_acceso_web[nombre] = ahora
                return {"status": "Permitido", "nombre": nombre, "diagnostico": errores}
            else:
                if "Desconocido" not in ultimo_acceso_web or ahora - ultimo_acceso_web["Desconocido"] > .5:
                    foto_nombre = f"web_{int(ahora)}.jpg"
                    foto_path_fisico = os.path.join(BASE_DIR, "capturas", foto_nombre)
                    cv2.imwrite(foto_path_fisico, frame)
                    guardado = cv2.imwrite(foto_path_fisico, frame)

                    print("Guardando en:", foto_path_fisico)
                    print("Guardado:", guardado)
                    # IMPORTANTE: Guardamos solo el nombre para el Dashboard
                    registrar_acceso("Desconocido", "N/A", "Denegado", foto_nombre) 
                    ultimo_acceso_web["Desconocido"] = ahora
                return {"status": "Desconocido", "diagnostico": errores}
    except Exception as e:
        print(f"🔥 Error: {e}")
        return {"error": str(e)}

# ===============================
# MONTAJES
# ===============================
app.mount("/capturas", StaticFiles(directory=os.path.join(BASE_DIR, "capturas")), name="capturas")
app.mount("/dashboard", StaticFiles(directory=os.path.join(BASE_DIR, "frontend/dashboard")), name="dashboard")
app.mount("/scan", StaticFiles(directory=os.path.join(BASE_DIR, "frontend/scan")), name="scan")
app.mount("/otp", StaticFiles(directory=os.path.join(BASE_DIR, "frontend/otp")), name="otp")
app.mount("/registro", StaticFiles(directory=os.path.join(BASE_DIR, "frontend/registro")), name="registro")