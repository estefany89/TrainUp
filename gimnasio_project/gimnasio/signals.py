from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario
from .email_service import EmailService
import random, string


@receiver(post_save, sender=User)
def crear_perfil_y_enviar_email(sender, instance, created, **kwargs):
    """
    Crea PerfilUsuario y envía email SOLO para socios.
    Para monitores, esto se maneja manualmente en la vista.
    """
    if created:
        # Verificar si es un monitor (por el email que coincide con Monitor)
        from .models import Monitor
        es_monitor = Monitor.objects.filter(email=instance.email).exists()

        if not es_monitor:
            # Es un socio: crear perfil y enviar email
            PerfilUsuario.objects.create(user=instance, rol='socio')

            # Generar contraseña aleatoria para el email
            password_generada = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            instance.set_password(password_generada)
            instance.save()

            # Enviar email de bienvenida
            EmailService.enviar_bienvenida_socio(instance, password_generada)