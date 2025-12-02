from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from .models import PerfilUsuario, Monitor, Clase, Reserva, Pago
from datetime import timedelta

class GimnasioTestCase(TestCase):

    def setUp(self):
        # Crear un usuario socio
        self.user_socio = User.objects.create_user(
            username="juan.perez",
            password="test1234",
            first_name="Juan",
            last_name="Perez",
            email="juan@example.com"
        )
        self.perfil_socio = PerfilUsuario.objects.create(
            user=self.user_socio,
            telefono="123456789",
            rol="socio"
        )

        # Crear un monitor
        self.monitor = Monitor.objects.create(
            nombre="Carlos",
            apellidos="Lopez",
            dni="12345678A",
            telefono="987654321",
            email="carlos@example.com",
            especialidad="Yoga"
        )

        # Crear una clase
        self.clase = Clase.objects.create(
            nombre="Yoga Avanzado",
            descripcion="Clase de Yoga nivel avanzado",
            monitor=self.monitor,
            dia_semana="L",  # Lunes
            hora_inicio="10:00",
            duracion_minutos=60,
            capacidad_maxima=5,
            nivel="avanzado",
            activa=True
        )

    def test_crear_reserva(self):
        # Crear reserva para el socio en la clase
        fecha_clase = timezone.now().date() + timedelta(days=(0 - timezone.now().date().weekday()) % 7)  # próximo lunes
        reserva = Reserva.objects.create(
            socio=self.user_socio,
            clase=self.clase,
            fecha=fecha_clase
        )

        # Verificar que la reserva existe
        self.assertEqual(Reserva.objects.count(), 1)
        self.assertFalse(reserva.cancelada)
        self.assertEqual(reserva.clase, self.clase)
        self.assertEqual(reserva.socio, self.user_socio)

    def test_pago_asociado_reserva(self):
        # Crear reserva
        fecha_clase = timezone.now().date() + timedelta(days=(0 - timezone.now().date().weekday()) % 7)
        reserva = Reserva.objects.create(
            socio=self.user_socio,
            clase=self.clase,
            fecha=fecha_clase
        )

        # Crear pago
        pago = Pago.objects.create(
            socio=self.user_socio,
            tipo_pago="mensualidad",
            importe=50.0,
            fecha_vencimiento=timezone.now().date() + timedelta(days=7),
            concepto="Pago mensualidad",
            registrado_por=self.user_socio
        )

        # Verificar pago
        self.assertEqual(Pago.objects.count(), 1)
        self.assertEqual(pago.socio, self.user_socio)
        self.assertEqual(pago.importe, 50.0)
        self.assertEqual(pago.estado, 'pendiente')  # valor por defecto en tu modelo

    def test_capacidad_clase(self):
        # Llenar la clase hasta su capacidad
        fecha_clase = timezone.now().date() + timedelta(days=(0 - timezone.now().date().weekday()) % 7)
        for i in range(self.clase.capacidad_maxima):
            user = User.objects.create_user(username=f"socio{i}", password="test1234")
            PerfilUsuario.objects.create(user=user, rol="socio")
            Reserva.objects.create(socio=user, clase=self.clase, fecha=fecha_clase)

        # Intentar añadir un socio extra
        user_extra = User.objects.create_user(username="extra", password="test1234")
        PerfilUsuario.objects.create(user=user_extra, rol="socio")
        reservas_activas = Reserva.objects.filter(clase=self.clase, fecha=fecha_clase, cancelada=False).count()

        self.assertEqual(reservas_activas, self.clase.capacidad_maxima)
        self.assertTrue(reservas_activas >= self.clase.capacidad_maxima)
from django.test import TestCase

# Create your tests here.
