import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Leer las variables del .env
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL")


def send_alert_email(to_email, subject, body):
    """Envía un correo de alerta usando SMTP"""

    try:
        # Crear el mensaje
        msg = EmailMessage()
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        # Conectarse al servidor SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # Cifra la conexión
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"✅ Correo enviado correctamente a {to_email}")

    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")



