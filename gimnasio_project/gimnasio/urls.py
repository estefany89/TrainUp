from django.urls import path
from . import views

app_name = 'gimnasio'

urlpatterns = [
    # ===== PÁGINAS PRINCIPALES =====
    path('', views.InicioView.as_view(), name='inicio'),

    # ===== AUTENTICACIÓN =====
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('registro/', views.RegistroView.as_view(), name='registro'),

    # ===== PERFIL USUARIO =====
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
    path('perfil/editar/', views.EditarPerfilView.as_view(), name='editar_perfil'),

    # ===== MONITORES =====
    path('monitores/', views.ListadoMonitoresView.as_view(), name='listado_monitores'),
    path('monitores/gestion/', views.GestionMonitoresView.as_view(), name='gestion_monitores'),
    path('monitores/<int:pk>/', views.DetalleMonitorView.as_view(), name='detalle_monitor'),
    path('monitores/<int:pk>/editar/', views.EditarMonitorView.as_view(), name='editar_monitor'),
    path('monitores/<int:pk>/alternar/', views.AlternarEstadoMonitorView.as_view(), name='alternar_monitor'),
    path('monitores/borrar/<int:pk>/', views.BorrarMonitorView.as_view(), name='borrar_monitor'),



    # ===== CLASES =====
    path('clases/', views.ListadoClasesView.as_view(), name='listado_clases'),
    path('clases/horario/', views.HorarioClasesView.as_view(), name='horario_clases'),
    path('clases/nueva/', views.NuevaClaseView.as_view(), name='nueva_clase'),
    path('clases/<int:pk>/', views.DetalleClaseView.as_view(), name='detalle_clase'),
    path('clases/<int:pk>/editar/', views.EditarClaseView.as_view(), name='editar_clase'),
    path('clases/<int:pk>/eliminar/', views.EliminarClaseView.as_view(), name='eliminar_clase'),

    # ===== RESERVAS =====
    path('reservas/', views.MisReservasView.as_view(), name='mis_reservas'),
    path('reservas/nueva/<int:clase_pk>/', views.NuevaReservaView.as_view(), name='nueva_reserva'),
    path('reservas/<int:pk>/cancelar/', views.CancelarReservaView.as_view(), name='cancelar_reserva'),

    # ===== PAGOS =====
    path('pagos/', views.MisPagosView.as_view(), name='mis_pagos'),
    path('pagos/<int:pk>/', views.DetallePagoView.as_view(), name='detalle_pago'),

    # ===== GESTIÓN SOCIOS (ADMIN) =====
    path('usuarios/', views.GestionSocioView.as_view(), name='gestion_usuarios'),
    path('usuarios/nuevo/', views.NuevoSocioView.as_view(), name='nuevo_usuario'),
    path('usuarios/<int:pk>/editar/', views.EditarSocioView.as_view(), name='editar_usuario'),
    path('usuarios/<int:pk>/desactivar/', views.DesactivarSocioView.as_view(), name='desactivar_usuario'),

    # ===== GESTIÓN PAGOS (ADMIN) =====
    path('admin/pagos/', views.GestionPagosView.as_view(), name='gestion_pagos'),
    path('admin/pagos/nuevo/', views.NuevoPagoView.as_view(), name='nuevo_pago'),
    path('admin/pagos/<int:pk>/marcar-pagado/', views.MarcarPagadoView.as_view(), name='marcar_pagado'),

    # ===== ADMIN - ASIGNAR CLASES A MONITORES =====
    path('admin/asignar-clases/', views.AsignarClasesMonitorView.as_view(), name='asignar_clases_monitor'),
    path('admin/clases-reservadas/', views.ClasesReservadasAdminView.as_view(), name='clases_reservadas'),

    # ===== MONITOR - SUS CLASES =====
    path('monitor/mis-clases/', views.MisClasesMonitorView.as_view(), name='mis_clases_monitor'),
    path('monitor/socios-apuntados/', views.SociosApuntadosView.as_view(), name='socios_apuntados'),

    # ===== ESTADÍSTICAS (ADMIN) =====
    path('estadisticas/', views.EstadisticasView.as_view(), name='estadisticas'),
    path('reportes/', views.ReportesView.as_view(), name='reportes'),


]

