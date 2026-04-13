import smtplib
from email.mime.text import MIMEText

# ⚠️ CONFIGURA ESTO
EMAIL_SENDER = "diegosp.ti24@utsjr.edu.mx"
EMAIL_PASSWORD = "pqjp mktd ljcr aocc"

def enviar_otp_email(destinatario, otp):

    asunto = "Código de acceso - BioAccess"
    
    mensaje = f"""
Hola 👋

Tu código de acceso de un solo uso es:

🔐 {otp}

Este código expira en 5 minutos.

Si no solicitaste este acceso, ignora este mensaje.

— BioAccess
"""

    msg = MIMEText(mensaje)
    msg["Subject"] = asunto
    msg["From"] = EMAIL_SENDER
    msg["To"] = destinatario

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("📧 OTP enviado correctamente a", destinatario)

    except Exception as e:
        print("❌ Error enviando correo:", e)