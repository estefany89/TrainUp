from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

# ---------------- Serializers ----------------
class RecuperarContrasenaSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetearContrasenaSerializer(serializers.Serializer):
    password1 = serializers.CharField()
    password2 = serializers.CharField()

class CambiarContrasenaSerializer(serializers.Serializer):
    password_actual = serializers.CharField()
    password_nueva = serializers.CharField()
    password_confirmar = serializers.CharField()


# ---------------- Recuperar contraseña ----------------
class RecuperarContrasenaAPI(generics.GenericAPIView):
    serializer_class = RecuperarContrasenaSerializer
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get(self, request):
        return Response({"email": ""})

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

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
            pass

        return Response({
            'message': 'Si el email existe, recibirás instrucciones para recuperar tu contraseña.'
        })


# ---------------- Resetear contraseña ----------------
class ResetearContrasenaAPI(generics.GenericAPIView):
    serializer_class = ResetearContrasenaSerializer
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get(self, request, uidb64, token):
        return Response({"password1": "", "password2": ""})

    def post(self, request, uidb64, token):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password1 = serializer.validated_data['password1']
        password2 = serializer.validated_data['password2']

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Enlace inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Enlace expirado o inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        if password1 != password2:
            return Response({'error': 'Las contraseñas no coinciden.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(password1) < 6:
            return Response({'error': 'Contraseña muy corta.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password1)
        user.save()
        return Response({'message': 'Contraseña actualizada correctamente.'})


# ---------------- Cambiar contraseña (usuario logueado) ----------------
class CambiarContrasenaAPI(generics.GenericAPIView):
    serializer_class = CambiarContrasenaSerializer
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "password_actual": "",
            "password_nueva": "",
            "password_confirmar": ""
        })

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        password_actual = serializer.validated_data['password_actual']
        password_nueva = serializer.validated_data['password_nueva']
        password_confirmar = serializer.validated_data['password_confirmar']

        if not user.check_password(password_actual):
            return Response({'error': 'Contraseña actual incorrecta.'}, status=status.HTTP_400_BAD_REQUEST)
        if password_nueva != password_confirmar:
            return Response({'error': 'Las contraseñas nuevas no coinciden.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(password_nueva) < 6:
            return Response({'error': 'Contraseña muy corta.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password_nueva)
        user.save()
        return Response({'message': 'Contraseña actualizada correctamente.'}, status=status.HTTP_200_OK)
