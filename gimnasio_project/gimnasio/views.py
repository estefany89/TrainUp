from django.db import models
from .email_service import EmailService
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta

from .models import PerfilUsuario, Monitor, Clase, Reserva, Pago
from .decorators import admin_required, socio_required


# ============================================
# AUTENTICACIÓN
# ============================================
class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('gimnasio:inicio')
        return render(request, 'gimnasio/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido/a {user.get_full_name() or user.username}!')
            return redirect('gimnasio:inicio')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return render(request, 'gimnasio/login.html')


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, 'Has cerrado sesión correctamente.')
        return redirect('gimnasio:login')


class RegistroView(View):
    def get(self, request):
        return render(request, 'gimnasio/registro.html')

    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        telefono = request.POST.get('telefono')
        dni = request.POST.get('dni')

        # Validaciones
        if password != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'gimnasio/registro.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return render(request, 'gimnasio/registro.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado.')
            return render(request, 'gimnasio/registro.html')

        # Crear usuario
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            first_name=nombre,
            last_name=apellidos
        )

        # Crear perfil
        PerfilUsuario.objects.create(
            user=user,
            telefono=telefono,
            dni=dni,
            rol='socio'
        )

        # -------------------------------
        # Enviar correo de bienvenida
        # -------------------------------
        from datetime import datetime
        from .email_service import EmailService

        template_data = {
            'name': f'{nombre} {apellidos}',
            'fecha': datetime.now().strftime("%d/%m/%Y")
        }

        try:
            email_service = EmailService(to_email=email, template_data=template_data)
            email_service.send()
        except Exception as e:
            print(f"Error enviando correo: {e}")

        messages.success(request, '¡Registro exitoso! Ya puedes iniciar sesión.')
        return redirect('gimnasio:login')


# ============================================
# PÁGINA DE INICIO
# ============================================
class InicioView(View):
    def get(self, request):
        context = {}

        if request.user.is_authenticated:
            perfil = getattr(request.user, 'perfil', None)

            # Clases próximas
            clases_activas = Clase.objects.filter(activa=True).order_by('dia_semana', 'hora_inicio')[:6]

            if perfil and perfil.rol == 'admin':
                # Dashboard admin
                context['es_admin'] = True
                context['total_socios'] = PerfilUsuario.objects.filter(rol='socio', activo=True).count()
                context['total_monitores'] = Monitor.objects.filter(activo=True).count()
                context['total_clases'] = Clase.objects.filter(activa=True).count()
                context['pagos_pendientes'] = Pago.objects.filter(estado='pendiente').count()
            else:
                # Dashboard socio
                context['es_admin'] = False
                context['mis_reservas'] = Reserva.objects.filter(
                    socio=request.user,
                    cancelada=False,
                    fecha__gte=timezone.now().date()
                ).order_by('fecha')[:5]
                context['pagos_pendientes'] = Pago.objects.filter(
                    socio=request.user,
                    estado='pendiente'
                ).count()

            context['clases_disponibles'] = clases_activas

        return render(request, 'gimnasio/inicio.html', context)


# ============================================
# PERFIL DE USUARIO
# ============================================
@method_decorator(login_required, name='dispatch')
class PerfilView(View):
    def get(self, request):
        perfil = get_object_or_404(PerfilUsuario, user=request.user)

        # Estadísticas del socio
        total_reservas = Reserva.objects.filter(socio=request.user).count()
        reservas_asistidas = Reserva.objects.filter(socio=request.user, asistio=True).count()
        pagos_realizados = Pago.objects.filter(socio=request.user, estado='pagado').count()

        context = {
            'perfil': perfil,
            'total_reservas': total_reservas,
            'reservas_asistidas': reservas_asistidas,
            'pagos_realizados': pagos_realizados,
        }

        return render(request, 'gimnasio/perfil.html', context)


@method_decorator(login_required, name='dispatch')
class EditarPerfilView(View):
    def get(self, request):
        perfil = get_object_or_404(PerfilUsuario, user=request.user)
        return render(request, 'gimnasio/editar_perfil.html', {'perfil': perfil})

    def post(self, request):
        perfil = get_object_or_404(PerfilUsuario, user=request.user)
        user = request.user

        # Actualizar datos del usuario
        user.first_name = request.POST.get('nombre')
        user.last_name = request.POST.get('apellidos')
        user.email = request.POST.get('email')
        user.save()

        # Actualizar datos del perfil
        perfil.telefono = request.POST.get('telefono')
        perfil.direccion = request.POST.get('direccion')
        perfil.fecha_nacimiento = request.POST.get('fecha_nacimiento') or None

        if request.FILES.get('foto'):
            perfil.foto = request.FILES['foto']

        perfil.save()

        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('gimnasio:perfil')


# ============================================
# MONITORES
# ============================================
class ListadoMonitoresView(ListView):
    model = Monitor
    template_name = 'gimnasio/listado_monitores.html'
    context_object_name = 'monitores'

    def get_queryset(self):
        queryset = Monitor.objects.filter(activo=True)

        especialidad = self.request.GET.get('especialidad')
        if especialidad:
            queryset = queryset.filter(especialidad=especialidad)

        return queryset.order_by('apellidos', 'nombre')


class DetalleMonitorView(DetailView):
    model = Monitor
    template_name = 'gimnasio/detalle_monitor.html'
    context_object_name = 'monitor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clases'] = Clase.objects.filter(
            monitor=self.object,
            activa=True
        ).order_by('dia_semana', 'hora_inicio')
        return context


@method_decorator([login_required, admin_required], name='dispatch')
class GestionMonitoresView(View):
    def get(self, request):
        monitores = Monitor.objects.all().order_by('-activo', 'apellidos', 'nombre')
        return render(request, 'gimnasio/gestion_monitores.html', {'monitores': monitores})

    def post(self, request):
        import random
        import string

        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        dni = request.POST.get('dni')
        telefono = request.POST.get('telefono')
        email = request.POST.get('email')
        especialidad = request.POST.get('especialidad')
        biografia = request.POST.get('biografia', '')

        # Validar DNI único
        if Monitor.objects.filter(dni=dni).exists():
            messages.error(request, 'Ya existe un monitor con ese DNI.')
            return redirect('gimnasio:gestion_monitores')

        # Validar email único
        if Monitor.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe un monitor con ese email.')
            return redirect('gimnasio:gestion_monitores')

        # Crear monitor
        monitor = Monitor.objects.create(
            nombre=nombre,
            apellidos=apellidos,
            dni=dni,
            telefono=telefono,
            email=email,
            especialidad=especialidad,
            biografia=biografia
        )

        if request.FILES.get('foto'):
            monitor.foto = request.FILES['foto']
            monitor.save()

        # Crear usuario y perfil para el monitor
        username = f"{nombre.lower()}.{apellidos.lower().split()[0]}"
        if User.objects.filter(username=username).exists():
            username = f"{username}{random.randint(1, 999)}"

        # Generar contraseña aleatoria
        password_generada = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password_generada),
            first_name=nombre,
            last_name=apellidos
        )

        PerfilUsuario.objects.create(
            user=user,
            telefono=telefono,
            dni=dni,
            rol='monitor'
        )

        # Enviar email de bienvenida
        email_enviado = EmailService.enviar_bienvenida_monitor(monitor, password_generada, username)

        if email_enviado:
            messages.success(request,
                             f'Monitor creado correctamente. Se ha enviado un email a {email} con las credenciales.')
        else:
            messages.warning(request,
                             f'Monitor creado correctamente, pero hubo un error al enviar el email. Usuario: {username}, Contraseña: {password_generada}')

        return redirect('gimnasio:gestion_monitores')

@method_decorator([login_required, admin_required], name='dispatch')
class EditarMonitorView(View):
    def get(self, request, pk):
        monitor = get_object_or_404(Monitor, pk=pk)
        return render(request, 'gimnasio/editar_monitor.html', {'monitor': monitor})

    def post(self, request, pk):
        monitor = get_object_or_404(Monitor, pk=pk)

        monitor.nombre = request.POST.get('nombre')
        monitor.apellidos = request.POST.get('apellidos')
        monitor.telefono = request.POST.get('telefono')
        monitor.email = request.POST.get('email')
        monitor.especialidad = request.POST.get('especialidad')
        monitor.biografia = request.POST.get('biografia', '')

        if request.FILES.get('foto'):
            monitor.foto = request.FILES['foto']

        monitor.save()

        messages.success(request, 'Monitor actualizado correctamente.')
        return redirect('gimnasio:detalle_monitor', pk=pk)


@method_decorator([login_required, admin_required], name='dispatch')
class AlternarEstadoMonitorView(View):
    def post(self, request, pk):
        monitor = get_object_or_404(Monitor, pk=pk)
        monitor.activo = not monitor.activo  # Alterna el estado
        monitor.save()

        estado = "activado" if monitor.activo else "desactivado"
        messages.success(request, f'Monitor {estado} correctamente.')
        return redirect('gimnasio:listado_monitores')


@method_decorator([login_required, admin_required], name='dispatch')
class BorrarMonitorView(View):
    def post(self, request, pk, *args, **kwargs):
        monitor = get_object_or_404(Monitor, pk=pk)
        nombre = monitor.nombre_completo
        monitor.delete()
        messages.error(request, f"El monitor {nombre} fue eliminado permanentemente.")
        return redirect('gimnasio:gestion_monitores')


# ============================================
# CLASES
# ============================================
class ListadoClasesView(ListView):
    model = Clase
    template_name = 'gimnasio/listado_clases.html'
    context_object_name = 'clases'

    def get_queryset(self):
        queryset = Clase.objects.filter(activa=True).select_related('monitor')

        # Filtros
        dia = self.request.GET.get('dia')
        nivel = self.request.GET.get('nivel')
        monitor_id = self.request.GET.get('monitor')

        if dia:
            queryset = queryset.filter(dia_semana=dia)
        if nivel:
            queryset = queryset.filter(nivel=nivel)
        if monitor_id:
            queryset = queryset.filter(monitor_id=monitor_id)

        return queryset.order_by('dia_semana', 'hora_inicio')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['monitores'] = Monitor.objects.filter(activo=True)
        return context


class HorarioClasesView(View):
    """Vista de horario semanal de clases"""

    def get(self, request):
        clases = Clase.objects.filter(activa=True).order_by('dia_semana', 'hora_inicio')

        # Organizar clases por día
        dias = {
            'L': 'Lunes',
            'M': 'Martes',
            'X': 'Miércoles',
            'J': 'Jueves',
            'V': 'Viernes',
            'S': 'Sábado',
            'D': 'Domingo'
        }

        horario = {}
        for codigo, nombre in dias.items():
            horario[nombre] = clases.filter(dia_semana=codigo)

        context = {'horario': horario}
        return render(request, 'gimnasio/horario_clases.html', context)


class DetalleClaseView(DetailView):
    model = Clase
    template_name = 'gimnasio/detalle_clase.html'
    context_object_name = 'clase'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Verificar si el usuario ya tiene reserva activa
        if self.request.user.is_authenticated:
            tiene_reserva = Reserva.objects.filter(
                socio=self.request.user,
                clase=self.object,
                cancelada=False,
                fecha__gte=timezone.now().date()
            ).exists()
            context['tiene_reserva'] = tiene_reserva

        # Próximas sesiones de esta clase (siguientes 4 semanas)
        proximas_fechas = []
        hoy = timezone.now().date()
        for i in range(28):  # 4 semanas
            fecha = hoy + timedelta(days=i)
            # Mapear día de la semana (0=Lunes, 6=Domingo)
            dia_codigo = ['L', 'M', 'X', 'J', 'V', 'S', 'D'][fecha.weekday()]
            if dia_codigo == self.object.dia_semana:
                proximas_fechas.append(fecha)

        context['proximas_fechas'] = proximas_fechas[:8]  # Solo mostrar 8
        return context


@method_decorator([login_required, admin_required], name='dispatch')
class NuevaClaseView(View):
    def get(self, request):
        monitores = Monitor.objects.filter(activo=True)
        return render(request, 'gimnasio/nueva_clase.html', {'monitores': monitores})

    def post(self, request):
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        monitor_id = request.POST.get('monitor')
        dia_semana = request.POST.get('dia_semana')
        hora_inicio = request.POST.get('hora_inicio')
        duracion_minutos = request.POST.get('duracion_minutos')
        capacidad_maxima = request.POST.get('capacidad_maxima')
        nivel = request.POST.get('nivel')
        sala = request.POST.get('sala', '')

        monitor = get_object_or_404(Monitor, pk=monitor_id) if monitor_id else None

        Clase.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            monitor=monitor,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            duracion_minutos=duracion_minutos,
            capacidad_maxima=capacidad_maxima,
            nivel=nivel,
            sala=sala
        )

        messages.success(request, 'Clase creada correctamente.')
        return redirect('gimnasio:listado_clases')


@method_decorator([login_required, admin_required], name='dispatch')
class EditarClaseView(View):
    def get(self, request, pk):
        clase = get_object_or_404(Clase, pk=pk)
        monitores = Monitor.objects.filter(activo=True)
        return render(request, 'gimnasio/editar_clase.html', {
            'clase': clase,
            'monitores': monitores
        })

    def post(self, request, pk):
        clase = get_object_or_404(Clase, pk=pk)

        clase.nombre = request.POST.get('nombre')
        clase.descripcion = request.POST.get('descripcion')
        monitor_id = request.POST.get('monitor')
        clase.monitor = get_object_or_404(Monitor, pk=monitor_id) if monitor_id else None
        clase.dia_semana = request.POST.get('dia_semana')
        clase.hora_inicio = request.POST.get('hora_inicio')
        clase.duracion_minutos = request.POST.get('duracion_minutos')
        clase.capacidad_maxima = request.POST.get('capacidad_maxima')
        clase.nivel = request.POST.get('nivel')
        clase.sala = request.POST.get('sala', '')

        clase.save()

        messages.success(request, 'Clase actualizada correctamente.')
        return redirect('gimnasio:detalle_clase', pk=pk)


@method_decorator([login_required, admin_required], name='dispatch')
class EliminarClaseView(View):
    def post(self, request, pk):
        clase = get_object_or_404(Clase, pk=pk)
        clase.activa = False
        clase.save()

        messages.success(request, 'Clase desactivada correctamente.')
        return redirect('gimnasio:listado_clases')


# ============================================
# RESERVAS
# ============================================
@method_decorator([login_required, socio_required], name='dispatch')
class MisReservasView(ListView):
    model = Reserva
    template_name = 'gimnasio/mis_reservas.html'
    context_object_name = 'reservas'

    def get_queryset(self):
        return Reserva.objects.filter(
            socio=self.request.user,
            cancelada=False
        ).select_related('clase', 'clase__monitor').order_by('-fecha')


@method_decorator([login_required, socio_required], name='dispatch')
class NuevaReservaView(View):
    def get(self, request, clase_pk):
        clase = get_object_or_404(Clase, pk=clase_pk, activa=True)

        # Calcular próximas fechas disponibles
        proximas_fechas = []
        hoy = timezone.now().date()
        for i in range(28):  # Próximas 4 semanas
            fecha = hoy + timedelta(days=i)
            dia_codigo = ['L', 'M', 'X', 'J', 'V', 'S', 'D'][fecha.weekday()]
            if dia_codigo == clase.dia_semana and fecha >= hoy:
                # Verificar si hay plazas disponibles
                reservas_esa_fecha = Reserva.objects.filter(
                    clase=clase,
                    fecha=fecha,
                    cancelada=False
                ).count()

                if reservas_esa_fecha < clase.capacidad_maxima:
                    proximas_fechas.append({
                        'fecha': fecha,
                        'disponibles': clase.capacidad_maxima - reservas_esa_fecha
                    })

        context = {
            'clase': clase,
            'proximas_fechas': proximas_fechas[:10]
        }
        return render(request, 'gimnasio/nueva_reserva.html', context)

    def post(self, request, clase_pk):
        clase = get_object_or_404(Clase, pk=clase_pk, activa=True)
        fecha_str = request.POST.get('fecha')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        # Verificar si ya tiene reserva para esa clase y fecha
        if Reserva.objects.filter(
                socio=request.user,
                clase=clase,
                fecha=fecha,
                cancelada=False
        ).exists():
            messages.error(request, 'Ya tienes una reserva para esta clase en esa fecha.')
            return redirect('gimnasio:nueva_reserva', clase_pk=clase_pk)

        # Verificar capacidad
        reservas_existentes = Reserva.objects.filter(
            clase=clase,
            fecha=fecha,
            cancelada=False
        ).count()

        if reservas_existentes >= clase.capacidad_maxima:
            messages.error(request, 'No hay plazas disponibles para esta fecha.')
            return redirect('gimnasio:nueva_reserva', clase_pk=clase_pk)

        # Crear reserva
        Reserva.objects.create(
            socio=request.user,
            clase=clase,
            fecha=fecha
        )

        messages.success(request, f'Reserva confirmada para {clase.nombre} el {fecha.strftime("%d/%m/%Y")}.')
        return redirect('gimnasio:mis_reservas')


@method_decorator([login_required, socio_required], name='dispatch')
class CancelarReservaView(View):
    def post(self, request, pk):
        reserva = get_object_or_404(Reserva, pk=pk, socio=request.user)

        # Verificar que la reserva sea futura
        if reserva.fecha < timezone.now().date():
            messages.error(request, 'No puedes cancelar una reserva pasada.')
            return redirect('gimnasio:mis_reservas')

        reserva.cancelar()

        messages.success(request, 'Reserva cancelada correctamente.')
        return redirect('gimnasio:mis_reservas')


# PAGOS Y GESTIÓN DE USUARIOS

# ============================================
# PAGOS (VISTA SOCIO)
# ============================================
@method_decorator([login_required, socio_required], name='dispatch')
class MisPagosView(ListView):
    model = Pago
    template_name = 'gimnasio/mis_pagos.html'
    context_object_name = 'pagos'

    def get_queryset(self):
        return Pago.objects.filter(socio=self.request.user).order_by('-fecha_emision')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_pendiente'] = Pago.objects.filter(
            socio=self.request.user,
            estado='pendiente'
        ).aggregate(total=models.Sum('importe'))['total'] or 0
        return context


@method_decorator([login_required, socio_required], name='dispatch')
class DetallePagoView(DetailView):
    model = Pago
    template_name = 'gimnasio/detalle_pago.html'
    context_object_name = 'pago'

    def get_queryset(self):
        return Pago.objects.filter(socio=self.request.user)


# ============================================
# GESTIÓN DE USUARIOS (ADMIN)
# ============================================
@method_decorator([login_required, admin_required], name='dispatch')
class GestionSocioView(ListView):
    model = PerfilUsuario
    template_name = 'gimnasio/gestion_socios.html'
    context_object_name = 'socios'
    paginate_by = 20

    def get_queryset(self):
        queryset = PerfilUsuario.objects.select_related('user').filter(rol='socio')

        # Filtros
        busqueda = self.request.GET.get('q')
        estado = self.request.GET.get('estado')

        if busqueda:
            queryset = queryset.filter(
                Q(user__username__icontains=busqueda) |
                Q(user__first_name__icontains=busqueda) |
                Q(user__last_name__icontains=busqueda) |
                Q(dni__icontains=busqueda)
            )

        if estado == 'activo':
            queryset = queryset.filter(activo=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(activo=False)

        return queryset.order_by('-fecha_registro')


@method_decorator([login_required, admin_required], name='dispatch')
class NuevoSocioView(View):
    def get(self, request):
        return render(request, 'gimnasio/nuevo_socio.html')

    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        telefono = request.POST.get('telefono')
        dni = request.POST.get('dni')
        rol = request.POST.get('rol', 'socio')

        # Validaciones
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return render(request, 'gimnasio/nuevo_socio.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado.')
            return render(request, 'gimnasio/nuevo_socio.html')

        # Crear usuario
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            first_name=nombre,
            last_name=apellidos
        )

        # Crear perfil
        PerfilUsuario.objects.create(
            user=user,
            telefono=telefono,
            dni=dni,
            rol=rol
        )

        messages.success(request, 'Usuario creado correctamente.')
        return redirect('gimnasio:gestion_usuarios')


@method_decorator([login_required, admin_required], name='dispatch')
class EditarSocioView(View):
    def get(self, request, pk):
        perfil = get_object_or_404(PerfilUsuario, pk=pk)
        return render(request, 'gimnasio/editar_usuario.html', {'perfil': perfil})

    def post(self, request, pk):
        perfil = get_object_or_404(PerfilUsuario, pk=pk)
        user = perfil.user

        # Actualizar datos del usuario
        user.first_name = request.POST.get('nombre')
        user.last_name = request.POST.get('apellidos')
        user.email = request.POST.get('email')
        user.save()

        # Actualizar datos del perfil
        perfil.telefono = request.POST.get('telefono')
        perfil.direccion = request.POST.get('direccion')
        perfil.save()

        messages.success(request, 'Usuario actualizado correctamente.')
        return redirect('gimnasio:gestion_usuarios')


@method_decorator([login_required, admin_required], name='dispatch')
class DesactivarSocioView(View):
    def post(self, request, pk):
        perfil = get_object_or_404(PerfilUsuario, pk=pk)
        perfil.activo = not perfil.activo
        perfil.save()

        estado = "activado" if perfil.activo else "desactivado"
        messages.success(request, f'Usuario {estado} correctamente.')
        return redirect('gimnasio:gestion_usuarios')


# ============================================
# GESTIÓN DE PAGOS (ADMIN)
# ============================================
@method_decorator([login_required, admin_required], name='dispatch')
class GestionPagosView(ListView):
    model = Pago
    template_name = 'gimnasio/gestion_pagos.html'
    context_object_name = 'pagos'
    paginate_by = 30

    def get_queryset(self):
        queryset = Pago.objects.select_related('socio').all()

        # Filtros
        estado = self.request.GET.get('estado')
        socio_id = self.request.GET.get('socio')
        mes = self.request.GET.get('mes')

        if estado:
            queryset = queryset.filter(estado=estado)
        if socio_id:
            queryset = queryset.filter(socio_id=socio_id)
        if mes:
            year, month = mes.split('-')
            queryset = queryset.filter(
                fecha_emision__year=year,
                fecha_emision__month=month
            )

        return queryset.order_by('-fecha_emision')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['socios'] = User.objects.filter(perfil__rol='socio', perfil__activo=True)

        # Totales
        context['total_pendiente'] = Pago.objects.filter(
            estado='pendiente'
        ).aggregate(total=models.Sum('importe'))['total'] or 0

        context['total_mes'] = Pago.objects.filter(
            estado='pagado',
            fecha_pago__month=timezone.now().month,
            fecha_pago__year=timezone.now().year
        ).aggregate(total=models.Sum('importe'))['total'] or 0

        return context


@method_decorator([login_required, admin_required], name='dispatch')
class NuevoPagoView(View):
    def get(self, request):
        socios = User.objects.filter(perfil__rol='socio', perfil__activo=True)
        return render(request, 'gimnasio/nuevo_pago.html', {'socios': socios})

    def post(self, request):
        socio_id = request.POST.get('socio')
        tipo_pago = request.POST.get('tipo_pago')
        importe = request.POST.get('importe')
        fecha_vencimiento = request.POST.get('fecha_vencimiento')
        concepto = request.POST.get('concepto')
        observaciones = request.POST.get('observaciones', '')

        socio = get_object_or_404(User, pk=socio_id)

        Pago.objects.create(
            socio=socio,
            tipo_pago=tipo_pago,
            importe=importe,
            fecha_vencimiento=fecha_vencimiento,
            concepto=concepto,
            observaciones=observaciones,
            registrado_por=request.user
        )

        messages.success(request, 'Pago registrado correctamente.')
        return redirect('gimnasio:gestion_pagos')


@method_decorator([login_required, admin_required], name='dispatch')
class MarcarPagadoView(View):
    def post(self, request, pk):
        pago = get_object_or_404(Pago, pk=pk)
        metodo_pago = request.POST.get('metodo_pago')

        pago.marcar_pagado(metodo_pago)

        messages.success(request, 'Pago marcado como pagado correctamente.')
        return redirect('gimnasio:gestion_pagos')


# ============================================
# ESTADÍSTICAS Y REPORTES (ADMIN)
# ============================================
@method_decorator([login_required, admin_required], name='dispatch')
class EstadisticasView(View):
    def get(self, request):
        # Estadísticas generales
        total_socios = PerfilUsuario.objects.filter(rol='socio', activo=True).count()
        total_monitores = Monitor.objects.filter(activo=True).count()
        total_clases = Clase.objects.filter(activa=True).count()

        # Estadísticas de reservas
        hoy = timezone.now().date()
        reservas_hoy = Reserva.objects.filter(fecha=hoy, cancelada=False).count()
        reservas_semana = Reserva.objects.filter(
            fecha__gte=hoy,
            fecha__lte=hoy + timedelta(days=7),
            cancelada=False
        ).count()

        # Estadísticas de pagos
        pagos_pendientes = Pago.objects.filter(estado='pendiente').count()
        ingresos_mes = Pago.objects.filter(
            estado='pagado',
            fecha_pago__month=hoy.month,
            fecha_pago__year=hoy.year
        ).aggregate(total=models.Sum('importe'))['total'] or 0

        # Clases más populares
        clases_populares = Clase.objects.filter(activa=True).annotate(
            num_reservas=Count('reservas')
        ).order_by('-num_reservas')[:5]

        context = {
            'total_socios': total_socios,
            'total_monitores': total_monitores,
            'total_clases': total_clases,
            'reservas_hoy': reservas_hoy,
            'reservas_semana': reservas_semana,
            'pagos_pendientes': pagos_pendientes,
            'ingresos_mes': ingresos_mes,
            'clases_populares': clases_populares,
        }

        return render(request, 'gimnasio/estadisticas.html', context)


# ============================================
# ADMIN - ASIGNAR CLASES A MONITORES
# ============================================
@method_decorator([login_required, admin_required], name='dispatch')
class AsignarClasesMonitorView(View):
    def get(self, request):
        monitores = Monitor.objects.filter(activo=True)
        clases = Clase.objects.filter(activa=True).order_by('dia_semana', 'hora_inicio')

        context = {
            'monitores': monitores,
            'clases': clases
        }
        return render(request, 'gimnasio/asignar_clases_monitor.html', context)

    def post(self, request):
        clase_id = request.POST.get('clase_id')
        monitor_id = request.POST.get('monitor_id')

        clase = get_object_or_404(Clase, pk=clase_id)

        if monitor_id:
            monitor = get_object_or_404(Monitor, pk=monitor_id)
            clase.monitor = monitor
            clase.save()
            messages.success(request, f'Clase "{clase.nombre}" asignada a {monitor.nombre_completo()}')
        else:
            clase.monitor = None
            clase.save()
            messages.info(request, f'Monitor removido de la clase "{clase.nombre}"')

        return redirect('gimnasio:asignar_clases_monitor')


# ============================================
# ADMIN - VER CLASES RESERVADAS
# ============================================
@method_decorator([login_required, admin_required], name='dispatch')
class ClasesReservadasAdminView(View):
    def get(self, request):
        # Obtener todas las reservas activas
        reservas = Reserva.objects.filter(
            cancelada=False,
            fecha__gte=timezone.now().date()
        ).select_related('socio', 'clase', 'clase__monitor').order_by('fecha', 'clase__hora_inicio')

        # Filtros opcionales
        clase_id = request.GET.get('clase')
        fecha = request.GET.get('fecha')

        if clase_id:
            reservas = reservas.filter(clase_id=clase_id)
        if fecha:
            reservas = reservas.filter(fecha=fecha)

        clases = Clase.objects.filter(activa=True)

        context = {
            'reservas': reservas,
            'clases': clases
        }
        return render(request, 'gimnasio/clases_reservadas_admin.html', context)


# ============================================
# MONITOR - MIS CLASES ASIGNADAS
# ============================================
@method_decorator(login_required, name='dispatch')
class MisClasesMonitorView(View):
    def get(self, request):
        # Verificar que sea monitor
        if request.user.perfil.rol != 'monitor':
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('gimnasio:inicio')

        # Obtener el monitor asociado al usuario
        try:
            monitor = Monitor.objects.get(email=request.user.email)
            mis_clases = Clase.objects.filter(
                monitor=monitor,
                activa=True
            ).order_by('dia_semana', 'hora_inicio')

            # Para cada clase, contar reservas
            clases_con_info = []
            hoy = timezone.now().date()

            for clase in mis_clases:
                total_reservas = Reserva.objects.filter(
                    clase=clase,
                    cancelada=False,
                    fecha__gte=hoy
                ).count()

                clases_con_info.append({
                    'clase': clase,
                    'total_reservas': total_reservas,
                    'plazas_libres': clase.capacidad_maxima - total_reservas
                })

            context = {
                'monitor': monitor,
                'clases_con_info': clases_con_info
            }

            return render(request, 'gimnasio/mis_clases_monitor.html', context)

        except Monitor.DoesNotExist:
            messages.error(request, 'No se encontró tu perfil de monitor. Contacta al administrador.')
            return redirect('gimnasio:inicio')


# ============================================
# MONITOR - SOCIOS APUNTADOS A MIS CLASES
# ============================================
@method_decorator(login_required, name='dispatch')
class SociosApuntadosView(View):
    def get(self, request):
        # Verificar que sea monitor
        if request.user.perfil.rol != 'monitor':
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('gimnasio:inicio')

        try:
            monitor = Monitor.objects.get(email=request.user.email)

            # Obtener todas las clases del monitor
            mis_clases = Clase.objects.filter(monitor=monitor, activa=True)

            # Obtener reservas futuras de esas clases
            hoy = timezone.now().date()
            reservas = Reserva.objects.filter(
                clase__in=mis_clases,
                cancelada=False,
                fecha__gte=hoy
            ).select_related('socio', 'clase').order_by('fecha', 'clase__hora_inicio')

            # Filtro por clase
            clase_id = request.GET.get('clase')
            if clase_id:
                reservas = reservas.filter(clase_id=clase_id)

            context = {
                'monitor': monitor,
                'reservas': reservas,
                'mis_clases': mis_clases
            }

            return render(request, 'gimnasio/socios_apuntados.html', context)

        except Monitor.DoesNotExist:
            messages.error(request, 'No se encontró tu perfil de monitor. Contacta al administrador.')
            return redirect('gimnasio:inicio')


@method_decorator([login_required, admin_required], name='dispatch')
class ReportesView(View):
    def get(self, request):
        # Generar reportes más detallados
        hoy = timezone.now().date()
        mes_actual = hoy.month
        year_actual = hoy.year

        # Reporte de asistencia por clase
        clases_con_asistencia = Clase.objects.filter(activa=True).annotate(
            total_reservas=Count('reservas', filter=Q(reservas__cancelada=False)),
            total_asistencias=Count('reservas', filter=Q(reservas__asistio=True))
        )

        # Reporte de ingresos por mes
        ingresos_por_mes = []
        for i in range(6):
            mes = hoy - timedelta(days=30 * i)
            total = Pago.objects.filter(
                estado='pagado',
                fecha_pago__month=mes.month,
                fecha_pago__year=mes.year
            ).aggregate(total=models.Sum('importe'))['total'] or 0
            ingresos_por_mes.append({
                'mes': mes.strftime('%B %Y'),
                'total': total
            })

        context = {
            'clases_con_asistencia': clases_con_asistencia,
            'ingresos_por_mes': ingresos_por_mes,
        }

        return render(request, 'gimnasio/reportes.html', context)