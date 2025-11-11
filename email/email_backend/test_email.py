from email_utils import send_alert_email

# Prueba: enviar correo de alerta
send_alert_email(
    to_email="jose.lescano868@gmail.com",
    subject="⚠️ Alerta de fallas recurrentes",
    body="Se ha detectado un 15% de defectos en el lote Nº 123. Por favor revisar la calibración."
)
