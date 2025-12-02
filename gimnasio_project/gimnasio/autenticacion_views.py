from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

# ---------------- Recuperar contraseña ----------------
class RecuperarContrasenaAPI(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get(self, request):
        # Permite mostrar el formulario en el navegador
        return Response({"email": ""})

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(
                f'/api/resetear-contrasena/{uid}/{token}/'
            )
            try:
                send_mail(
                    'Recuperar contraseña',
                    f'Enlace: {reset_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
            except Exception:
                print(f'Link de recuperación: {reset_link}')

        except User.DoesNotExist:
            pass  # No revelar si el email existe

        return Response({'message': 'Si el email existe, recibirás instrucciones para recuperar tu contraseña.'})


# ---------------- Resetear contraseña ----------------
class ResetearContrasenaAPI(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get(self, request, uidb64, token):
        # Formulario en el navegador
        return Response({"password1": "", "password2": ""})

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Enlace inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Enlace expirado o inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        password1 = request.data.get('password1')
        password2 = request.data.get('password2')

        if password1 != password2:
            return Response({'error': 'Las contraseñas no coinciden.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(password1) < 6:
            return Response({'error': 'Contraseña muy corta.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password1)
        user.save()
        return Response({'message': 'Contraseña actualizada correctamente.'})


# ---------------- Cambiar contraseña (usuario logueado) ----------------
class CambiarContrasenaAPI(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "password_actual": "",
            "password_nueva": "",
            "password_confirmar": ""
        })

    def post(self, request):
        user = request.user
        password_actual = request.data.get('password_actual')
        password_nueva = request.data.get('password_nueva')
        password_confirmar = request.data.get('password_confirmar')

        if not user.check_password(password_actual):
            return Response({'error': 'Contraseña actual incorrecta.'}, status=status.HTTP_400_BAD_REQUEST)
        if password_nueva != password_confirmar:
            return Response({'error': 'Las contraseñas nuevas no coinciden.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(password_nueva) < 6:
            return Response({'error': 'Contraseña muy corta.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password_nueva)
        user.save()
        return Response({'message': 'Contraseña actualizada correctamente.'}, status=status.HTTP_200_OK)
