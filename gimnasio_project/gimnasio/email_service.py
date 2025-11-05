from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class EmailService:
    SENDGRID_API_KEY = '***REMOVED***'  # Tu API Key real
    FROM_EMAIL = '***REMOVED***'  # Tu correo verificado en SendGrid
    TEMPLATE_ID_BIENVENIDA = '***REMOVED***'  # Tu Template ID real

    def __init__(self, to_email, template_id=None, template_data=None):
        self.to_email = to_email
        self.template_id = template_id or self.TEMPLATE_ID_BIENVENIDA
        self.template_data = template_data or {}

    def send(self):
        message = Mail(
            from_email=self.FROM_EMAIL,
            to_emails=self.to_email
        )
        message.template_id = self.template_id
        message.dynamic_template_data = self.template_data

        try:
            sg = SendGridAPIClient(self.SENDGRID_API_KEY)
            response = sg.send(message)
            print(f'Correo enviado: {response.status_code}')
        except Exception as e:
            print(f'Error al enviar correo: {e}')
