# src/core/roles.py
class Roles:
    DRAGON = 'dragon'
    ADMIN = 'admin_platform' # Ser más específico para roles de plataforma
    # Roles para Tenants
    TENANT_ADMIN = 'tenant_admin'
    TENANT_EDITOR = 'tenant_editor'
    TENANT_MEMBER = 'tenant_member'
    # ... otros roles que necesites ...

    @classmethod
    def get_all_system_roles(cls): # Ejemplo de un helper
        return [cls.DRAGON, cls.ADMIN]