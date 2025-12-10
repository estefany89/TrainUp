# TrainUp Gym

## 1. Introducción

### 1.1. Descripción del Proyecto
TrainUp Gym es una app web que hace fácil la gestión de gimnasios. Socios, monitores y administradores tienen todo lo que necesitan: clases, reservas y pagos, cada uno según su rol.

### 1.2. Objetivos

**Objetivo General:**  
Desarrollar un sistema web completo que permita la gestión integral de un gimnasio, desde la administración de usuarios hasta el control de pagos y generación de reportes estadísticos.  

**Objetivos Específicos:**
- Implementar un sistema de autenticación robusto con gestión de roles (Administrador, Monitor, Socio).  
- Desarrollar un módulo de gestión de clases con asignación de monitores y control de capacidad.  
- Crear un sistema de reservas en tiempo real con validación de disponibilidad.  
- Implementar gestión completa de pagos con generación de facturas en PDF.  
- Integrar servicios externos para recuperación de contraseñas y rutinas de ejercicio.  
- Proporcionar dashboards personalizados según el rol del usuario.  
- Generar reportes estadísticos y de ingresos.  

### 1.3. Alcance

**Para Administradores:**
- Gestión completa de monitores (alta, baja, edición).  
- Gestión de socios y sus perfiles.  
- Creación y administración de clases.  
- Control de pagos y generación de cuotas.  
- Visualización de estadísticas y reportes.  
- Asignación de clases a monitores.  

**Para Monitores:**
- Visualización de clases asignadas.  
- Consulta de socios inscritos en sus clases.  
- Gestión de perfil personal.  

**Para Socios:**
- Reserva y cancelación de clases.  
- Consulta de rutinas de ejercicios.  
- Visualización de pagos y descarga de facturas.  
- Acceso a descuentos en marcas asociadas.  
- Gestión de perfil personal.  

## 2. Principales Componentes

**Vistas principales**

| Nombre de la vista | Descripción breve |
|-------------------|-----------------|
| LoginView | Permite a los usuarios autenticarse en el sistema. |
| LogoutView | Cierra la sesión del usuario. |
| InicioView | Página principal; muestra dashboard distinto para admin y socio, incluyendo estadísticas y próximas clases. |
| PerfilView | Muestra el perfil del usuario, incluyendo estadísticas de reservas y pagos. |
| EditarPerfilView | Permite al usuario editar su perfil y foto. |
| ListadoMonitoresView | Lista todos los monitores activos, con opción de filtrado por especialidad. |
| GestionMonitoresView | Vista de administración para crear nuevos monitores y enviar credenciales por email. |
| EditarMonitorView | Permite editar los datos de un monitor existente. |
| AlternarEstadoMonitorView | Activa o desactiva un monitor. |
| BorrarMonitorView | Elimina un monitor permanentemente. |
| ListadoClasesView | Muestra todas las clases activas, con filtros por día, nivel o monitor. |
| NuevaClaseView | Permite a un admin crear una nueva clase. |
| EditarClaseView | Permite editar una clase existente. |
| EliminarClaseView | Desactiva una clase. |
| MisReservasView | Permite a los socios ver sus reservas y reservar nuevas plazas. |
| CancelarReservaView | Permite cancelar reservas futuras. |
| MisPagosView | Muestra al socio sus pagos pendientes y realizados. |
| DetallePagoView | Detalle de un pago específico del socio. |
| GenerarFacturaView | Genera y descarga factura PDF de un pago. |
| GestionSocioView | Vista admin para listar, filtrar y gestionar socios. |
| NuevoSocioView | Permite al admin crear un nuevo socio. |
| DetalleSocioView | Permite al admin ver y editar los datos de un socio. |
| DesactivarSocioView | Activa o desactiva un socio. |
| GestionPagosView | Vista admin para listar, filtrar y gestionar pagos. |
| NuevoPagoView | Permite al admin registrar un nuevo pago para un socio. |
| MarcarPagadoView | Permite al admin marcar un pago como pagado y registrar el método de pago. |
| EstadisticasView | Muestra estadísticas generales de socios, monitores, clases, reservas y pagos. |
| AsignarClasesMonitorView | Permite asignar o remover monitores de las clases. |
| ClasesReservadasAdminView | Lista todas las reservas activas, con opción de filtrado por clase o fecha. |
| MisClasesMonitorView | Vista para que un monitor vea sus clases asignadas y plazas disponibles. |
| SociosApuntadosView | Vista para que un monitor vea los socios apuntados a sus clases futuras. |
| ReporteAsistenciaView | Genera un reporte de asistencia de las clases. |
| ReporteIngresosView | Genera un reporte de ingresos de los últimos 6 meses. |
| RutinasSocioView | Muestra la página de rutinas para el socio. |
| RutinasAPI | Obtiene rutinas desde la API externa de wger y devuelve datos procesados para la interfaz. |

**Tests**

| Nombre del test | Descripción breve |
|-----------------|-----------------|
| setUp | Configura los datos iniciales: crea un usuario socio, un monitor y una clase. |
| test_crear_reserva | Verifica que un socio puede crear una reserva correctamente y que no esté cancelada. |
| test_pago_asociado_reserva | Comprueba que un pago puede asociarse a un socio con importe correcto y estado inicial "pendiente". |
| test_capacidad_clase | Verifica que la clase no puede superar su capacidad máxima. |

## 3. Instalación y Despliegue

### Requisitos
- Docker & Docker Compose  
- Git  
- Cuenta AWS  

### Desarrollo Local
```bash
git clone https://github.com/tu-usuario/TrainUp.git
cd TrainUp.git


### Documentación API
- [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)  
- [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)  

### Ejemplo de uso
1. El admin registra un nuevo socio o monitor; se generan credenciales y se envía un email con acceso.  
2. El admin crea clases y asigna monitores.  
3. Los socios reservan clases, consultan rutinas y realizan pagos de sus cuotas.  
4. Los monitores visualizan las clases asignadas y los socios inscritos.  
5. El admin genera reportes de ingresos y de asistencia para análisis estadístico.  

### Próximas mejoras
- Implementación de notificaciones y chat en tiempo real.  
- Dashboards con gráficos interactivos para todos los roles.  
- Recordatorios automáticos de pagos pendientes.  
- Álbum de fotos generado automáticamente al final de cada ciclo de clases.  
