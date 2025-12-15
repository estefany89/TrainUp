# TrainUp Gym

## 1. Introducción

### Descripción del Proyecto
TrainUp Gym es una app web que hace fácil la gestión de gimnasios. Socios, monitores y administradores tienen todo lo que necesitan: clases, reservas y pagos, cada uno según su rol.

### Objetivos

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

### Alcance

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
## 2. Estructura del proyecto


```text
gimnasio_project/              # Raíz del repositorio
├── gimnasio/                  # Configuración principal de Django
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── app/                        # App principal
│   ├── migrations/             # Migraciones de la base de datos
│   ├── models.py               # Definición de modelos
│   ├── views.py                # Vistas basadas en clases y funciones
│   ├── forms.py                # Formularios personalizados
│   ├── tests.py                # Pruebas automatizadas
│   ├── urls.py                 # Rutas específicas de la app
│   └── templates/app/          # Plantillas HTML
├── static/                     # CSS, JS e imágenes estáticas
├── media/                      # Archivos subidos por usuarios
├── staticfiles/                # Archivos estáticos recolectados
├── db.sqlite3                  # Base de datos SQLite
├── descargar_imagenes.py       # Script auxiliar para descargas de imágenes
├── Dockerfile                  # Dockerfile para despliegue
├── docker-compose.yml          # Configuración de servicios Docker
├── docker-entrypoint.sh        # Script de entrada para Docker
├── deploy.sh                   # Script de despliegue
├── gimnasio_config/            # Configuraciones adicionales del proyecto
├── initial_data.json           # Datos iniciales de la base de datos
├── manage.py                   # Comandos de Django
├── nginx.conf                  # Configuración de Nginx
├── requirements.txt
```


## 2. Principales Componentes

**Vistas principales**

| Vista | Descripción | Vista | Descripción | Vista | Descripción |
|-------|------------|-------|------------|-------|------------|
| LoginView | Autenticación de usuarios | LogoutView | Cierre de sesión | InicioView | Dashboard con estadísticas y próximas clases |
| PerfilView | Perfil del usuario | EditarPerfilView | Editar perfil y foto | ListadoMonitoresView | Lista de monitores con filtros |
| GestionMonitoresView | Admin: crear/editar monitores | EditarMonitorView | Editar monitor | AlternarEstadoMonitorView | Activar/desactivar monitor |
| BorrarMonitorView | Elimina un monitor | ListadoClasesView | Lista clases activas con filtros | NuevaClaseView | Crear nueva clase |
| EditarClaseView | Editar clase existente | EliminarClaseView | Desactivar clase | MisReservasView | Ver y gestionar reservas de socio |
| CancelarReservaView | Cancelar reservas futuras | MisPagosView | Pagos pendientes y realizados | DetallePagoView | Detalle de pago específico |
| GenerarFacturaView | Generar PDF de pago | GestionSocioView | Admin: listar y gestionar socios | NuevoSocioView | Crear nuevo socio |
| DetalleSocioView | Ver/editar datos de socio | DesactivarSocioView | Activar/desactivar socio | GestionPagosView | Admin: listar y gestionar pagos |
| NuevoPagoView | Registrar pago nuevo | MarcarPagadoView | Marcar pago como pagado | EstadisticasView | Estadísticas generales |
| AsignarClasesMonitorView | Asignar/remover monitores de clases | ClasesReservadasAdminView | Listar reservas activas | MisClasesMonitorView | Monitor: clases asignadas y plazas |
| SociosApuntadosView | Monitor: ver socios de sus clases | ReporteAsistenciaView | Reporte asistencia de clases | ReporteIngresosView | Reporte de ingresos últimos 6 meses |
| RutinasSocioView | Rutinas del socio | RutinasAPI | Obtener rutinas de API externa | | |

**Tests**

| Nombre del test | Descripción breve |
|-----------------|-----------------|
| setUp | Configura los datos iniciales: crea un usuario socio, un monitor y una clase. |
| test_crear_reserva | Verifica que un socio puede crear una reserva correctamente y que no esté cancelada. |
| test_pago_asociado_reserva | Comprueba que un pago puede asociarse a un socio con importe correcto y estado inicial "pendiente". |
| test_capacidad_clase | Verifica que la clase no puede superar su capacidad máxima. |

**Plantillas HTML**

| Archivo | Descripción | Archivo | Descripción | Archivo | Descripción |
|---------|------------|---------|------------|---------|------------|
| asignar_clases_monitor.html | Asignar clases a socios | base.html | Plantilla base | clases_reservadas_admin.html | Clases reservadas admin |
| descuentos.html | Gestionar descuentos | detalle_socio.html | Detalles de un socio | editar_clase.html | Editar clase existente |
| estadisticas.html | Visualizar estadísticas | gestion_socios.html | Administración de socios | gestion_monitores.html | Administración de monitores |
| gestion_pagos.html | Gestionar pagos | inicio.html | Página principal | listado_clases.html | Listado de clases |
| listado_monitores.html | Listado de monitores | login.html | Inicio de sesión | mis_clases_monitor.html | Clases de un monitor |
| mis_pagos.html | Pagos de un socio | mis_reservas.html | Reservas de un socio | nueva_clase.html | Crear nueva clase |
| nuevo_pago.html | Registrar pago | nuevo_socio.html | Registrar socio | perfil.html | Perfil de usuario |
| reporte_asistencia.html | Reporte de asistencia | reporte_ingresos.html | Reporte de ingresos | reportes.html | Vista general de reportes |
| rutinas_socio.html | Rutinas asignadas | socios_apuntados.html | Socios por clase | | |



**Modelos**

| Nombre del modelo | Relaciones principales | Descripción breve |
|------------------|----------------------|-----------------|
| PerfilUsuario | user (OneToOne a User) | Perfil extendido de usuario con rol, datos personales y foto |
| Monitor | clases (1 a N) | Información de monitores, especialidad, foto y estado activo |
| Clase | monitor (FK), reservas (1 a N) | Clases de gimnasio, con horario, nivel, capacidad y monitor asignado |
| Reserva | socio (FK), clase (FK) | Registro de reservas de socios para clases, con estado de asistencia y cancelación |
| Pago | socio (FK), registrado_por (FK) | Pagos/cuotas de socios, con tipo, importe, estado y método de pago |

## 3. Instalación y Despliegue

### Requisitos
- Docker & Docker Compose  
- Git  
- Cuenta AWS  

### Desarrollo Local
#### 1. Clonar el repositorio
```bash

git clone https://github.com/tu-usuario/TrainUp.git
cd TrainUp.git
```
#### 2. Copiar y configurar variables de entorno en .env
POSTGRES_DB
POSTGRES_USERs
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT
DJANGO_SECRET_KEY
SENDGRID_API_KEY
FROM_EMAIL
TEMPLATE_ID_BIENVENIDA_SOCIO
#### 3. Levantar servicios:
```
docker-compose up -d
```
#### 4. Aplicar migraciones y crear superusuario:
```
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```
#### 5. Acceder a la app en http://localhost:8000/trainup/ o en el caso de tener dominio, en el dominio.
### Documentación API
- [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)  
- [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)  

### Ejemplo de uso
1. El admin registra un nuevo socio se generan credenciales y se envía un email con acceso.
2. El admin registra un monitor y le asigna su usuario y contraseña
3. El admin crea clases y asigna monitores.  
4. Los socios reservan clases, consultan rutinas y realizan pagos de sus cuotas.  
5. Los monitores visualizan las clases asignadas y los socios inscritos.  
6. El admin genera reportes de ingresos y de asistencia para análisis estadístico.  

### Próximas mejoras
- Implementación de notificaciones y chat en tiempo real.  
- Recordatorios automáticos de pagos pendientes.  
- Analice rutinas frecuentes del socio y recomiende ejercicios.
 
