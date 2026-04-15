import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh

def detectar_liveness(frame):
    try:
        if frame is None:
            return False

        with mp_face_mesh.FaceMesh(static_image_mode=False) as face_mesh:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if not results.multi_face_landmarks:
                return False

            # 🔥 Validación extra: variación de imagen (movimiento)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            variacion = np.std(gray)

            # Si la imagen es muy "plana" → probablemente foto
            if variacion < 10:
                return False

            return True

    except Exception as e:
        print("Error en liveness:", e)
        return False
