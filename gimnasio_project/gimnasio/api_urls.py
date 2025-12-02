# gimnasio/api_urls.py
from django.urls import path
from . import autenticacion_views  # donde están tus APIs

urlpatterns = [
    # Recuperación de contraseña
    path('recuperar-contrasena/', autenticacion_views.RecuperarContrasenaAPI.as_view(), name='api_recuperar_contrasena'),
    path('resetear-contrasena/<uidb64>/<token>/', autenticacion_views.ResetearContrasenaAPI.as_view(), name='api_resetear_contrasena'),
    path('cambiar-contrasena/', autenticacion_views.CambiarContrasenaAPI.as_view(), name='api_cambiar_contrasena'),
]
