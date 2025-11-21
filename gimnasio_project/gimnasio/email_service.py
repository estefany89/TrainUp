from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
#llama a .env de contraseñas


class EmailService:
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    FROM_EMAIL = os.environ.get('FROM_EMAIL')
    TEMPLATE_ID_BIENVENIDA = os.environ.get('TEMPLATE_ID_BIENVENIDA')

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
            print(f'Correo enviado a {self.to_email}: Status {response.status_code}')
            return True
        except Exception as e:
            print(f'Error al enviar correo a {self.to_email}: {e}')
            return False

    @classmethod
    def enviar_bienvenida_socio(cls, user, password_generada):
        """Envía email de bienvenida cuando el admin registra un socio"""
        email_service = cls(
            to_email=user.email,
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

    @classmethod
    def enviar_bienvenida_monitor(cls, monitor, password_generada, username):
        """Envía email de bienvenida cuando el admin registra un monitor"""
        email_service = cls(
            to_email=monitor.email,
            template_data={
                'nombre': monitor.nombre,
                'apellidos': monitor.apellidos,
                'username': username,
                'password': password_generada,
                'email': monitor.email,
                'tipo_usuario': 'Monitor',
                'especialidad': monitor.get_especialidad_display()
            }
        )
        return email_service.send()