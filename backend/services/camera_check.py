import cv2
import numpy as np

def autodiagnostico_camara(frame):
    """
    Analiza la calidad de la imagen de forma optimizada.
    """
    diagnosticos = []
    
    # Redimensionar para agilizar calculos matematicos
    pequena = cv2.resize(frame, (160, 120))
    gray = cv2.cvtColor(pequena, cv2.COLOR_BGR2GRAY)
    
    # Analisis de Iluminacion
    brillo_promedio = np.mean(gray)
    
    if brillo_promedio < 50:
        diagnosticos.append("ALERTA: Poca iluminacion detectada") 
    elif brillo_promedio > 220:
        diagnosticos.append("ALERTA: Mucha iluminacion (Imagen quemada)") 
    
    # Analisis de nitidez
    varianza = cv2.Laplacian(gray, cv2.CV_64F).var()
    if varianza < 100:
        diagnosticos.append("AVISO: Imagen borrosa. Limpie la camara") 

    # Camara obstruida
    if brillo_promedio < 10:
        diagnosticos.append("ERROR: Camara obstruida") 

    return diagnosticos

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    print("Iniciando autodiagnostico optimizado...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        errores = autodiagnostico_camara(frame)
        
        y0, dy = 30, 30
        for i, linea in enumerate(errores):
            y = y0 + i * dy
            cv2.putText(frame, linea, (10, y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow("Autodiagnostico BioAccess", frame)
        
        if cv2.waitKey(1) & 0xFF == 27:
            break
        
    cap.release()
    cv2.destroyAllWindows()