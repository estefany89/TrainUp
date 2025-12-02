from django.db import models
from django.http import HttpResponse
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
from django.db.models import Q, Count, Sum
from datetime import datetime, timedelta
from django.db import IntegrityError, transaction

# Importaciones para PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from io import BytesIO

from .models import PerfilUsuario, Monitor, Clase, Reserva, Pago
from .decorators import admin_required, socio_required
from .email_service import EmailService

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

        # Validación para evitar None o vacíos
        if not username or not password:
            messages.error(request, 'Debes ingresar usuario y contraseña.')
            return render(request, 'gimnasio/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido/a {user.get_full_name() or user.username}!')
            return redirect('gimnasio:inicio')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return render(request, 'gimnasio/login.html')


# ============================================
# CERRAR SESIÓN
# ============================================
class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "Has cerrado sesión correctamente.")
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
        return redirect('gimnasio:gestion_monitores')


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
        # Solo mostrar clases activas con monitores activos
        queryset = Clase.objects.filter(activa=True, monitor__activo=True).select_related('monitor')

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

        # corregi los dias de la semana
        dia_semana_choices = Clase._meta.get_field('dia_semana').choices
        nivel_choices = Clase._meta.get_field('nivel').choices

        return render(request, 'gimnasio/editar_clase.html', {
            'clase': clase,
            'monitores': monitores,
            'dia_semana_choices': dia_semana_choices,
            'nivel_choices': nivel_choices,
        })

    def post(self, request, pk):
        clase = get_object_or_404(Clase, pk=pk)

        # Actualizar campos desde el formulario
        clase.nombre = request.POST.get('nombre')
        clase.descripcion = request.POST.get('descripcion')
        monitor_id = request.POST.get('monitor')
        clase.monitor = get_object_or_404(Monitor, pk=monitor_id) if monitor_id else None

        dia_semana = request.POST.get('dia_semana')
        if not dia_semana:
            messages.error(request, 'Debes seleccionar un día de la semana.')
            return redirect('gimnasio:editar_clase', pk=pk)
        clase.dia_semana = dia_semana

        clase.hora_inicio = request.POST.get('hora_inicio')
        clase.duracion_minutos = request.POST.get('duracion_minutos')
        clase.capacidad_maxima = request.POST.get('capacidad_maxima')
        clase.nivel = request.POST.get('nivel')
        clase.sala = request.POST.get('sala', '')

        clase.save()
        messages.success(request, 'Clase actualizada correctamente.')
        return redirect('gimnasio:listado_clases')


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
class MisReservasView(View):
    template_name = 'gimnasio/mis_reservas.html'

    def get(self, request):
        # Listar reservas actuales
        reservas = Reserva.objects.filter(
            socio=request.user,
            cancelada=False
        ).select_related('clase', 'clase__monitor').order_by('-fecha')

        # Preparar próximas clases disponibles
        proximas_clases = []
        hoy = timezone.now().date()
        # Solo mostrar clases con monitores activos
        clases_activas = Clase.objects.filter(
            activa=True,
            monitor__activo=True
        ).order_by('dia_semana', 'hora_inicio')

        dias = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        for clase in clases_activas:
            fechas_disponibles = []
            for i in range(28):  # Próximas 4 semanas
                fecha = hoy + timedelta(days=i)
                if dias[fecha.weekday()] == clase.dia_semana:
                    reservas_fecha = Reserva.objects.filter(
                        clase=clase,
                        fecha=fecha,
                        cancelada=False
                    ).count()
                    if reservas_fecha < clase.capacidad_maxima:
                        fechas_disponibles.append({
                            'fecha': fecha,
                            'disponibles': clase.capacidad_maxima - reservas_fecha
                        })
            if fechas_disponibles:
                proximas_clases.append({'clase': clase, 'fechas': fechas_disponibles[:10]})

        context = {
            'reservas': reservas,
            'proximas_clases': proximas_clases,
            'today': timezone.now().date(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        clase_id = request.POST.get('clase_id')
        fecha_str = request.POST.get('fecha')

        clase = get_object_or_404(Clase, pk=clase_id, activa=True)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        # Verificar si ya existe una reserva activa para este socio, clase y fecha
        reserva_existente = Reserva.objects.filter(
            socio=request.user,
            clase=clase,
            fecha=fecha,
            cancelada=False
        ).first()

        if reserva_existente:
            messages.error(request, 'Ya tienes una reserva para esta clase en esa fecha.')
            return redirect('gimnasio:mis_reservas')

        # Verificar si hay plazas disponibles (solo contando reservas activas)
        reservas_activas = Reserva.objects.filter(
            clase=clase,
            fecha=fecha,
            cancelada=False
        ).count()

        if reservas_activas >= clase.capacidad_maxima:
            messages.error(request, 'No hay plazas disponibles para esta fecha.')
            return redirect('gimnasio:mis_reservas')

        # Verificar si existe una reserva cancelada para reutilizarla
        reserva_cancelada = Reserva.objects.filter(
            socio=request.user,
            clase=clase,
            fecha=fecha,
            cancelada=True
        ).first()

        if reserva_cancelada:
            # Reactivar la reserva cancelada
            reserva_cancelada.cancelada = False
            reserva_cancelada.save()
            messages.success(request, f'Reserva reactivada para {clase.nombre} el {fecha.strftime("%d/%m/%Y")}.')
        else:
            # Crear nueva reserva
            Reserva.objects.create(socio=request.user, clase=clase, fecha=fecha)
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


@method_decorator([login_required, socio_required], name='dispatch')
class GenerarFacturaView(View):
    """Vista para generar y descargar factura en PDF de un pago"""

    def get(self, request, pk):
        # Obtener el pago y verificar que pertenece al usuario
        pago = get_object_or_404(Pago, pk=pk, socio=request.user)

        # Verificar que el pago esté pagado
        if pago.estado != 'pagado':
            messages.error(request, 'Este pago aún no ha sido procesado.')
            return redirect('gimnasio:mis_pagos')

        # Crear el PDF en memoria
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#FF6B35'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        # Título
        elements.append(Paragraph("FACTURA", title_style))
        elements.append(Spacer(1, 0.3 * inch))

        # Información del gimnasio
        gym_info = [
            ["TrainUp Gym"],
            ["Calle Fitness, 123"],
            ["11403 Jerez de la Frontera"],
            ["CIF: B12345678"],
            ["Tel: +34 123 456 789"]
        ]
        gym_table = Table(gym_info, colWidths=[3 * inch])
        gym_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),  # Primera fila en negrita
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (0, 0), 12),  # Nombre del gym más grande
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(gym_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Información de la factura
        factura_data = [
            ["Número de Factura:", f"FAC-{pago.id:05d}"],
            ["Fecha de Emisión:", pago.fecha_emision.strftime("%d/%m/%Y")],
            ["Fecha de Pago:", pago.fecha_pago.strftime("%d/%m/%Y") if pago.fecha_pago else "N/A"],
        ]
        factura_table = Table(factura_data, colWidths=[2 * inch, 3 * inch])
        factura_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(factura_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Información del cliente
        cliente_info = [
            ["CLIENTE"],
            [f"{pago.socio.get_full_name() or pago.socio.username}"],
            [f"Email: {pago.socio.email}"],
        ]
        cliente_table = Table(cliente_info, colWidths=[5 * inch])
        cliente_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F0F0')),
        ]))
        elements.append(cliente_table)
        elements.append(Spacer(1, 0.5 * inch))

        # Detalle del pago
        detalle_data = [
            ["Concepto", "Importe"],
            [pago.concepto, f"{pago.importe:.2f}€"],
        ]
        detalle_table = Table(detalle_data, colWidths=[4 * inch, 1.5 * inch])
        detalle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(detalle_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Total
        total_data = [
            ["TOTAL", f"{pago.importe:.2f}€"],
        ]
        total_table = Table(total_data, colWidths=[4 * inch, 1.5 * inch])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#FF6B35')),
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#FF6B35')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(total_table)
        elements.append(Spacer(1, 0.5 * inch))

        # Nota de agradecimiento
        nota = Paragraph(
            "<i>Gracias por confiar en TrainUp.</i>",
            ParagraphStyle('nota', alignment=TA_CENTER, fontSize=10, textColor=colors.grey)
        )
        elements.append(nota)

        # Construir PDF
        doc.build(elements)

        # Preparar respuesta
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Factura_{pago.id}_{pago.socio.username}.pdf"'

        return response


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
        queryset = PerfilUsuario.objects.filter(rol='socio').order_by('-fecha_registro')
        search = self.request.GET.get('search')
        estado = self.request.GET.get('estado')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(dni__icontains=search)
            )
        if estado in ['activo', 'inactivo']:
            queryset = queryset.filter(activo=(estado == 'activo'))
        return queryset


@method_decorator([login_required, admin_required], name='dispatch')
class NuevoSocioView(View):
    def get(self, request):
        return render(request, 'gimnasio/nuevo_socio.html')

    def post(self, request):
        import random
        import string

        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        dni = request.POST.get('dni')

        # Generar username automáticamente
        username = f"{nombre.lower()}.{apellidos.lower().split()[0]}"
        if User.objects.filter(username=username).exists():
            username = f"{username}{random.randint(1, 999)}"

        # Validar email único
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado.')
            return render(request, 'gimnasio/nuevo_socio.html')

        # Generar contraseña aleatoria
        password_generada = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # Crear usuario
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password_generada),
            first_name=nombre,
            last_name=apellidos
        )

        # Crear perfil de socio
        PerfilUsuario.objects.create(
            user=user,
            telefono=telefono,
            dni=dni,
            rol='socio'
        )

        # Enviar email con credenciales
        email_enviado = EmailService.enviar_bienvenida_socio(user, password_generada)

        if email_enviado:
            messages.success(request, f'Socio creado correctamente. Se ha enviado un email con las credenciales.')
        else:
            messages.warning(request, f'Socio creado, pero hubo un error al enviar el email. Usuario: {username}, Contraseña: {password_generada}')

        return redirect('gimnasio:gestion_socios')

@method_decorator([login_required, admin_required], name='dispatch')
class DetalleSocioView(View):
    def get(self, request, pk):
        perfil = get_object_or_404(PerfilUsuario, pk=pk)
        return render(request, 'gimnasio/detalle_socio.html', {'perfil': perfil})

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

        # Actualizar campo activo desde el checkbox
        perfil.activo = 'activo' in request.POST

        # foto
        if request.FILES.get('foto'):
            perfil.foto = request.FILES['foto']

        perfil.save()

        messages.success(request, 'Usuario actualizado correctamente.')
        return redirect('gimnasio:gestion_socios')

@method_decorator([login_required, admin_required], name='dispatch')
class DesactivarSocioView(View):
    def post(self, request, pk):
        perfil = get_object_or_404(PerfilUsuario, pk=pk)
        perfil.activo = not perfil.activo
        perfil.save()

        estado = "activado" if perfil.activo else "desactivado"
        messages.success(request, f'Usuario {estado} correctamente.')
        return redirect('gimnasio:gestion_socios')

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
            # Diccionario para meses en español
            meses = {
                'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5,
                'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9,
                'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
            }

            try:
                # Intentar formato YYYY-MM
                year, month = mes.split('-')
                queryset = queryset.filter(
                    fecha_emision__year=int(year),
                    fecha_emision__month=int(month)
                )
            except ValueError:
                # Si no es YYYY-MM, intentar nombre de mes
                month_number = meses.get(mes.capitalize())
                if month_number:
                    queryset = queryset.filter(fecha_emision__month=month_number)

        # Siempre devolver un queryset, nunca None
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
@method_decorator([login_required, admin_required], name='dispatch')
class MarcarPagadoView(View):
    def post(self, request, pk):
        pago = get_object_or_404(Pago, pk=pk)

        # Obtener método de pago enviado desde el formulario
        metodo_pago = request.POST.get('metodo_pago', 'efectivo')

        # Actualizar estado del pago
        pago.estado = 'pagado'
        pago.metodo_pago = metodo_pago
        pago.fecha_pago = timezone.now()
        pago.save()

        messages.success(request, 'El pago ha sido marcado como pagado correctamente.')
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



# Reporte de Asistencia por Clases
@method_decorator([login_required, admin_required], name='dispatch')
class ReporteAsistenciaView(View):
    def get(self, request):
        clases_con_asistencia = Clase.objects.filter(activa=True).annotate(
            total_reservas=Count('reservas', filter=Q(reservas__cancelada=False)),
            total_asistencias=Count('reservas', filter=Q(reservas__asistio=True))
        )
        context = {
            'clases_con_asistencia': clases_con_asistencia,
        }
        return render(request, 'gimnasio/reporte_asistencia.html', context)

# Reporte de Ingresos de los últimos 6 meses
@method_decorator([login_required, admin_required], name='dispatch')
class ReporteIngresosView(View):
    def get(self, request):
        hoy = timezone.now().date()
        ingresos_por_mes = []
        total_acumulado = 0
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
            total_acumulado += total
        context = {
            'ingresos_por_mes': ingresos_por_mes,
            'total_acumulado': total_acumulado,
        }
        return render(request, 'gimnasio/reporte_ingresos.html', context)