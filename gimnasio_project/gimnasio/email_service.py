from decouple import config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging

logger = logging.getLogger(__name__)

class EmailService:
    SENDGRID_API_KEY = config('SENDGRID_API_KEY')
    FROM_EMAIL = config('FROM_EMAIL')
    TEMPLATE_ID_BIENVENIDA_SOCIO = config('TEMPLATE_ID_BIENVENIDA_SOCIO')

    def __init__(self, to_email, template_id, template_data=None):
        self.to_email = to_email
        self.template_id = template_id
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
            logger.info(f'✅ Correo enviado a {self.to_email}: Status {response.status_code}')
            logger.info(f'Template ID usado: {self.template_id}')
            logger.info(f'Datos del template: {self.template_data}')
            return True
        except Exception as e:
            logger.error(f'❌ Error al enviar correo a {self.to_email}: {str(e)}')
            return False

    @classmethod
    def enviar_bienvenida_socio(cls, user, password_generada):
        """Envía email de bienvenida cuando el admin registra un socio"""
        logger.info(f'📧 Intentando enviar email de bienvenida a socio: {user.email}')

        email_service = cls(
            to_email=user.email,
            template_id=cls.TEMPLATE_ID_BIENVENIDA_SOCIO,
            template_data={
                'nombre': user.first_name,
                'apellidos': user.last_name,
                'username': user.username,
                'password': password_generada,
                'email': user.email,
                'tipo_usuario': 'Socio'
            }
        )
        return email_service.send()
