from django.contrib import admin
from .models import PerfilUsuario, Monitor, Clase, Reserva, Pago


# ===============================
# PERFIL USUARIO
# ===============================
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['user', 'rol', 'telefono', 'activo', 'fecha_registro']
    list_filter = ['rol', 'activo', 'fecha_registro']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'dni', 'telefono']
    readonly_fields = ['fecha_registro']

    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'rol', 'activo')
        }),
        ('Datos Personales', {
            'fields': ('dni', 'telefono', 'fecha_nacimiento', 'direccion', 'foto')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_registro',)
        }),
    )


# ===============================
# MONITOR
# ===============================
@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'especialidad', 'telefono', 'email', 'activo', 'fecha_contratacion']
    list_filter = ['especialidad', 'activo', 'fecha_contratacion']
    search_fields = ['nombre', 'apellidos', 'dni', 'email']
    readonly_fields = ['fecha_contratacion']

    fieldsets = (
        ('Datos Personales', {
            'fields': ('nombre', 'apellidos', 'dni', 'fecha_contratacion', 'foto')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email')
        }),
        ('Información Profesional', {
            'fields': ('especialidad', 'biografia', 'activo')
        }),
    )


# ===============================
# CLASE
# ===============================
@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'monitor', 'dia_semana', 'hora_inicio', 'duracion_minutos',
                    'capacidad_maxima', 'nivel', 'activa']
    list_filter = ['dia_semana', 'nivel', 'activa', 'monitor']
    search_fields = ['nombre', 'descripcion', 'sala']

    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'descripcion', 'nivel', 'activa')
        }),
        ('Horario y Ubicación', {
            'fields': ('dia_semana', 'hora_inicio', 'duracion_minutos', 'sala')
        }),
        ('Monitor y Capacidad', {
            'fields': ('monitor', 'capacidad_maxima')
        }),
    )


# ===============================
# RESERVA
# ===============================
@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['socio', 'clase', 'fecha', 'asistio', 'cancelada', 'fecha_reserva']
    list_filter = ['asistio', 'cancelada', 'fecha', 'clase']
    search_fields = ['socio__username', 'socio__first_name', 'socio__last_name', 'clase__nombre']
    readonly_fields = ['fecha_reserva', 'fecha_cancelacion']

    fieldsets = (
        ('Información de la Reserva', {
            'fields': ('socio', 'clase', 'fecha')
        }),
        ('Estado', {
            'fields': ('asistio', 'cancelada', 'fecha_cancelacion')
        }),
        ('Registro', {
            'fields': ('fecha_reserva',)
        }),
    )


# ===============================
# PAGO
# ===============================
@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['socio', 'concepto', 'importe', 'tipo_pago', 'estado',
                    'fecha_emision', 'fecha_vencimiento', 'fecha_pago']
    list_filter = ['estado', 'tipo_pago', 'metodo_pago', 'fecha_emision']
    search_fields = ['socio__username', 'socio__first_name', 'socio__last_name', 'concepto']
    readonly_fields = ['fecha_emision']

    fieldsets = (
        ('Información del Pago', {
            'fields': ('socio', 'tipo_pago', 'concepto', 'importe')
        }),
        ('Fechas', {
            'fields': ('fecha_emision', 'fecha_vencimiento', 'fecha_pago')
        }),
        ('Estado y Método', {
            'fields': ('estado', 'metodo_pago')
        }),
        ('Observaciones', {
            'fields': ('observaciones', 'registrado_por')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)