from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario
from .email_service import EmailService
import random, string

# Signal para crear PerfilUsuario y enviar email al crear un User
@receiver(post_save, sender=User)
def crear_perfil_y_enviar_email(sender, instance, created, **kwargs):
    if created:
        # Crear perfil (rol por defecto: socio, puedes ajustar)
        PerfilUsuario.objects.create(user=instance, rol='socio')

        # Generar contraseña aleatoria para el email
        password_generada = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        instance.set_password(password_generada)  # Guardar la contraseña generada
        instance.save()

        # Enviar email de bienvenida
        EmailService.enviar_bienvenida_socio(instance, password_generada)
