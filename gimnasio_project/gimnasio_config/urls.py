from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importar vistas de drf-spectacular
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Endpoints de tu app gimnasio
    path('', include('gimnasio.urls')),
    path('api/', include('gimnasio.api_urls')),

    # Endpoint del esquema OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Endpoint de documentación interactiva (Swagger UI)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# Servir archivos media y static en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
