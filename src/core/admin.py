# src/core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Tenant, CustomUser, UserRole, UserProfile, UserRoleAssignment, AuditLog, Notification
from django.utils.translation import gettext_lazy as _ # Para traducciones

class CustomUserAdmin(BaseUserAdmin):
    # Añade 'tenant' a los list_display, fieldsets, etc. si quieres verlo/editarlo en el admin
    list_display = ('username', 'email', 'tenant', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'tenant')
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Tenant Info'), {'fields': ('tenant',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Tenant Info'), {'fields': ('tenant',)}),
    )

admin.site.register(Tenant)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserRole)
admin.site.register(UserProfile)
admin.site.register(UserRoleAssignment)
admin.site.register(AuditLog)
admin.site.register(Notification)