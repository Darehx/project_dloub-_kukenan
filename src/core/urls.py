# src/core/urls.py
from django.urls import path, include
from rest_framework_nested import routers
from rest_framework.routers import DefaultRouter # <--- Importa DefaultRouter
from .views import auth_views, user_views, tenant_views, role_views
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

# Router principal para endpoints de nivel superior en 'core'
core_router = DefaultRouter()
core_router.register(r'tenants', tenant_views.TenantViewSet, basename='tenant')
core_router.register(r'roles', role_views.UserRoleViewSet, basename='role')
core_router.register(r'role-assignments', role_views.UserRoleAssignmentViewSet, basename='role-assignment')
# NO registres 'users' aquí si lo vas a usar como base para NestedSimpleRouter.
# O si lo haces, asegúrate de que no haya conflicto de prefijos.

# Router base para 'users' (puede ser SimpleRouter si solo es para anidar)
users_base_router = routers.SimpleRouter()
users_base_router.register(r'users', user_views.UserViewSet, basename='user')

# Router anidado para 'profile' bajo 'users'
users_profile_router = routers.NestedSimpleRouter(users_base_router, r'users', lookup='user')
users_profile_router.register(r'profile', user_views.UserProfileViewSet, basename='user-profile-nested')

app_name = 'core'

urlpatterns = [
    path('', include(core_router.urls)),         # <--- Incluye el DefaultRouter
    path('', include(users_base_router.urls)),   # Incluye el router base de usuarios
    path('', include(users_profile_router.urls)),# Incluye el router anidado de perfiles

    # URLs de autenticación
    path('auth/login/', auth_views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/check/', auth_views.CheckAuthView.as_view(), name='check_auth'),

    # URL específica para el usuario autenticado
    path('users/me/', user_views.UserMeView.as_view(), name='user_me'),
]