# config/urls.py
from django.contrib import admin
from django.urls import path, include # Asegúrate de importar include
from django.conf import settings # Para servir media en DEBUG
from django.conf.urls.static import static # Para servir media en DEBUG

# Importar vistas de simplejwt directamente aquí o donde prefieras,
# pero ya las tienes referenciadas en src/core/urls.py, lo cual está bien.
# from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API v1 Routes
    # Incluir las URLs de tu app 'core' bajo el prefijo 'api/v1/core/'
    # Django buscará un archivo urls.py dentro de la app src.core
    path('api/v1/core/', include('src.core.urls', namespace='core-api')),

    # Incluir las URLs de tu app 'ds_owari'
    path('api/v1/internal/', include('src.ds_owari.urls', namespace='ds_owari-api')), # 'internal' es un buen prefijo

    # Incluir las URLs para los módulos (ejemplo para CRM)
    path('api/v1/modules/crm/', include('src.modules.crm.urls', namespace='crm-api')),
    path('api/v1/modules/projects/', include('src.modules.project_management.urls', namespace='project_management-api')),
    path('api/v1/modules/finances/', include('src.modules.finances.urls', namespace='finances-api')),
    # path('api/v1/modules/dashboard/', include('src.modules.dashboard_module.urls', namespace='dashboard-api')),
    # path('api/v1/modules/service-catalog/', include('src.modules.service_catalog_management.urls', namespace='service_catalog-api')),


    # (Opcional pero recomendado) Si usas drf-spectacular para la documentación OpenAPI/Swagger
    # path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/v1/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # path('api/v1/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Servir archivos media durante el desarrollo (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Si también quieres que Django sirva los archivos estáticos en desarrollo
    # (útil si no usas whitenoise o similar y no quieres ejecutar collectstatic constantemente)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # STATIC_ROOT se define en prod, aquí sería para testearlo.
                                                                                # Mejor usar los finders por defecto de Django en dev.

    # (Opcional) Para el login/logout de la API Navegable de DRF si usas SessionAuthentication en DESARROLLO
    # if 'rest_framework.authentication.SessionAuthentication' in settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', []):
    #    urlpatterns += [
    #        path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    #    ]