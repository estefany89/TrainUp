from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator


# ===============================
# PERFIL DE USUARIO (ROL)
# ===============================
class PerfilUsuario(models.Model):
    ROLES = (
        ('admin', 'Administrador'),
        ('monitor', 'Monitor'),
        ('socio', 'Socio'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefono = models.CharField(max_length=15, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    dni = models.CharField(max_length=20, unique=True, null=True, blank=True)
    foto = models.ImageField(upload_to='usuarios/', null=True, blank=True)
    rol = models.CharField(max_length=10, choices=ROLES, default='socio')
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_rol_display()}"

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"


# ===============================
# MONITOR
# ===============================
class Monitor(models.Model):
    ESPECIALIDADES = (
        ('yoga', 'Yoga'),
        ('pilates', 'Pilates'),
        ('spinning', 'Spinning'),
        ('zumba', 'Zumba'),
        ('funcional', 'Entrenamiento Funcional'),
        ('musculacion', 'Musculación'),
        ('boxeo', 'Boxeo'),
        ('crossfit', 'CrossFit'),
        ('natacion', 'Natación'),
        ('otra', 'Otra'),
    )

    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    especialidad = models.CharField(max_length=20, choices=ESPECIALIDADES)
    fecha_contratacion = models.DateField(default=timezone.now)
    activo = models.BooleanField(default=True)
    # biografia eliminado
    foto = models.ImageField(upload_to='monitores/', null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellidos} - {self.get_especialidad_display()}"

    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}"

    class Meta:
        verbose_name = "Monitor"
        verbose_name_plural = "Monitores"
        ordering = ['apellidos', 'nombre']


# ===============================
# CLASE
# ===============================
class Clase(models.Model):
    DIAS_SEMANA = (
        ('L', 'Lunes'),
        ('M', 'Martes'),
        ('X', 'Miércoles'),
        ('J', 'Jueves'),
        ('V', 'Viernes'),
        ('S', 'Sábado'),
        ('D', 'Domingo'),
    )

    NIVELES = (
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
        ('todos', 'Todos los niveles'),
    )

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    monitor = models.ForeignKey(Monitor, on_delete=models.SET_NULL, null=True, related_name='clases')
    dia_semana = models.CharField(max_length=1, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    duracion_minutos = models.IntegerField(validators=[MinValueValidator(15)])
    capacidad_maxima = models.IntegerField(validators=[MinValueValidator(1)])
    nivel = models.CharField(max_length=15, choices=NIVELES, default='todos')
    activa = models.BooleanField(default=True)
    sala = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.nombre} - {self.get_dia_semana_display()} {self.hora_inicio.strftime('%H:%M')}"

    def plazas_disponibles(self):
        """Calcula las plazas disponibles para la próxima sesión"""
        reservas_activas = self.reservas.filter(
            cancelada=False,
            fecha__gte=timezone.now().date()
        ).count()
        return self.capacidad_maxima - reservas_activas

    def esta_completa(self):
        """Verifica si la clase está completa"""
        return self.plazas_disponibles() <= 0

    class Meta:
        verbose_name = "Clase"
        verbose_name_plural = "Clases"
        ordering = ['dia_semana', 'hora_inicio']


# ===============================
# RESERVA
# ===============================
class Reserva(models.Model):
    socio = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas')
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='reservas')
    fecha = models.DateField()
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    asistio = models.BooleanField(default=False)
    cancelada = models.BooleanField(default=False)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        estado = "Cancelada" if self.cancelada else ("Asistió" if self.asistio else "Pendiente")
        return f"{self.socio.username} - {self.clase.nombre} ({self.fecha}) - {estado}"

    def cancelar(self):
        """Cancela la reserva"""
        self.cancelada = True
        self.fecha_cancelacion = timezone.now()
        self.save()

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha', '-fecha_reserva']
        unique_together = ['socio', 'clase', 'fecha']


# ===============================
# PAGO/CUOTA
# ===============================
class Pago(models.Model):
    TIPOS_PAGO = (
        ('mensual', 'Cuota Mensual'),
        ('trimestral', 'Cuota Trimestral'),
        ('anual', 'Cuota Anual'),
        ('matricula', 'Matrícula'),
        ('clase_extra', 'Clase Extra'),
        ('otro', 'Otro'),
    )

    METODOS_PAGO = (
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('domiciliacion', 'Domiciliación'),
    )

    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
    )

    socio = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagos')
    tipo_pago = models.CharField(max_length=15, choices=TIPOS_PAGO)
    importe = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    fecha_emision = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField()
    fecha_pago = models.DateField(null=True, blank=True)
    metodo_pago = models.CharField(max_length=15, choices=METODOS_PAGO, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')
    concepto = models.CharField(max_length=200)
    observaciones = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pagos_registrados'
    )

    def __str__(self):
        return f"{self.socio.username} - {self.concepto} ({self.importe}€) - {self.get_estado_display()}"

    def marcar_pagado(self, metodo):
        """Marca el pago como pagado"""
        self.estado = 'pagado'
        self.fecha_pago = timezone.now().date()
        self.metodo_pago = metodo
        self.save()

    def esta_vencido(self):
        """Verifica si el pago está vencido"""
        return self.estado == 'pendiente' and self.fecha_vencimiento < timezone.now().date()

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_emision']
