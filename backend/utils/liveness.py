import cv2
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh

def detectar_liveness(frame):
    try:
        if frame is None:
            return False

        with mp_face_mesh.FaceMesh(static_image_mode=True) as face_mesh:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if not results.multi_face_landmarks:
                return False

            return True

    except Exception as e:
        print("Error en liveness:", e)
        return False