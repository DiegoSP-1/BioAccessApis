import cv2
import os
import numpy as np
import json
from backend.config.firebase_config import db
from backend.services.user_service import registrar_usuario

dataset_path = "dataset"

faces = []
labels = []
label_dict = {}

current_label = 0

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

print("Cargando dataset...")

for person in os.listdir(dataset_path):

    person_path = os.path.join(dataset_path, person)

    if not os.path.isdir(person_path):
        continue

    print(f"Procesando usuario: {person}")

    label_dict[current_label] = person

    # Guardar usuario en Firebase si no existe
    registrar_usuario(person)

    for image_name in os.listdir(person_path):

        image_path = os.path.join(person_path, image_name)

        image = cv2.imread(image_path)

        if image is None:
            print(f"No se pudo cargar {image_path}")
            continue

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        faces_detected = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces_detected:

            face = gray[y:y+h, x:x+w]

            faces.append(face)
            labels.append(current_label)

    current_label += 1

print("Entrenando modelo...")

recognizer = cv2.face.LBPHFaceRecognizer_create()

recognizer.train(faces, np.array(labels))

# Guardar modelo
os.makedirs("model", exist_ok=True)
recognizer.save("model/modelo.yml")

# Guardar etiquetas
with open("model/labels.json", "w") as f:
    json.dump(label_dict, f)

print("Modelo entrenado correctamente")
print("Modelo guardado en model/modelo.yml")
print("Etiquetas guardadas en model/labels.json")