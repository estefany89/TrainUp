from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario
from .email_service import EmailService
import random, string

@receiver(post_save, sender=User)
def crear_perfil_y_enviar_email(sender, instance, created, **kwargs):
    """
    Crea PerfilUsuario automáticamente:
    - Superuser → rol 'admin' (puede gestionar todo)
    - Usuario normal → rol 'socio' + email de bienvenida
    - Monitores → se gestionan manualmente
    """
    if not created:
        return

    # Superuser → administrador con acceso completo
    if instance.is_superuser:
        PerfilUsuario.objects.get_or_create(
            user=instance,
            defaults={'rol': 'admin', 'activo': True}  # ← CAMBIO: 'admin' en vez de 'administrador'
        )
        return

    # Verificar si es monitor
    from .models import Monitor
    if Monitor.objects.filter(email=instance.email).exists():
        return  # Monitores no se crean automáticamente

    # Crear socio normal
    PerfilUsuario.objects.create(user=instance, rol='socio')

    # Generar contraseña aleatoria
    password_generada = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    instance.set_password(password_generada)
    instance.save(update_fields=['password'])

    # Enviar email de bienvenida
    EmailService.enviar_bienvenida_socio(instance, password_generada)