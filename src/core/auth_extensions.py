# src/core/auth_extensions.py
import logging
from .models.role import UserRole # Asumiendo que UserRole está en src/core/models/role.py
# from .models.user import UserProfile # Si UserProfile está en src/core/models/user.py
# Si UserProfile se define después de CustomUser en el mismo archivo, no se puede importar así directamente.
# En ese caso, UserProfile se accedería vía self.profile dentro de los métodos.

# Importa tus constantes de roles
try:
    from .roles import Roles # Asume roles.py está en src/core/
except ImportError:
    class Roles: DRAGON = 'dragon'; # Placeholder
    print("ADVERTENCIA: src/core/roles.py no encontrado en auth_extensions. Usando roles placeholder.")

logger = logging.getLogger(__name__)

def add_user_role_methods(UserModel):
    # --- Propiedades y Métodos para Roles (Con Caché) ---
    @property
    def primary_role_obj(self): # Renombrado de 'primary_role' para evitar conflicto con un posible campo
        cache_key = '_primary_role_cache_obj'
        if not hasattr(self, cache_key):
            role = None
            try:
                # Asume que UserProfile se accede vía self.profile y ya está cargado/disponible
                # y que UserProfile está en src/core/models/user.py y tiene el campo primary_role
                from .models.user import UserProfile # Importación tardía
                profile_instance = UserProfile.objects.select_related('primary_role').get(user=self)
                if profile_instance.primary_role and profile_instance.primary_role.is_active:
                    role = profile_instance.primary_role
            except UserProfile.DoesNotExist:
                logger.debug(f"UserProfile no encontrado para usuario {self.pk} en primary_role_obj.")
            except Exception as e:
                logger.warning(f"Excepción accediendo a primary_role para {self.pk}: {e}")
            setattr(self, cache_key, role)
        return getattr(self, cache_key)

    @property
    def primary_role_name(self):
        role = self.primary_role_obj
        return role.name if role else None

    @property
    def get_secondary_active_roles(self):
        cache_key = '_secondary_roles_cache_obj'
        if not hasattr(self, cache_key):
            primary_role_instance_id = None
            primary_role_inst = self.primary_role_obj
            if primary_role_inst:
                primary_role_instance_id = primary_role_inst.id

            qs = UserRole.objects.none()
            if self.pk:
                # UserRoleAssignment debe estar importado o definido
                from .models.role import UserRoleAssignment
                qs = UserRole.objects.filter(
                    secondary_assignments__user_id=self.pk,
                    secondary_assignments__is_active=True,
                    is_active=True
                ).distinct()
                if primary_role_instance_id:
                    qs = qs.exclude(id=primary_role_instance_id)
            setattr(self, cache_key, qs)
        return getattr(self, cache_key)

    @property
    def get_secondary_active_role_names(self):
        return list(self.get_secondary_active_roles.values_list('name', flat=True))

    @property
    def get_all_active_role_names(self):
        all_roles = set(self.get_secondary_active_role_names)
        p_role_name = self.primary_role_name
        if p_role_name:
            all_roles.add(p_role_name)
        return sorted(list(all_roles)) # Es bueno tener un orden consistente

    def has_role(self, role_name_or_names):
        if not role_name_or_names:
            return False

        current_roles = self.get_all_active_role_names
        if isinstance(role_name_or_names, str):
            return role_name_or_names in current_roles
        elif isinstance(role_name_or_names, (list, tuple, set)):
            return any(r_name in current_roles for r_name in role_name_or_names)
        return False


    def is_dragon(self):
        dragon_role_name = getattr(Roles, 'DRAGON', None)
        return self.has_role(dragon_role_name) if dragon_role_name else False

    # Añadir los métodos/propiedades a la clase UserModel si no existen ya
    # Esto evita errores si ready() se llama múltiples veces (aunque no debería)
    if not hasattr(UserModel, 'primary_role_obj'):
        UserModel.add_to_class("primary_role_obj", primary_role_obj)
    if not hasattr(UserModel, 'primary_role_name'):
        UserModel.add_to_class("primary_role_name", primary_role_name)
    if not hasattr(UserModel, 'get_secondary_active_roles'):
        UserModel.add_to_class("get_secondary_active_roles", get_secondary_active_roles)
    if not hasattr(UserModel, 'get_secondary_active_role_names'):
        UserModel.add_to_class("get_secondary_active_role_names", get_secondary_active_role_names)
    if not hasattr(UserModel, 'get_all_active_role_names'):
        UserModel.add_to_class("get_all_active_role_names", get_all_active_role_names)
    if not hasattr(UserModel, 'has_role'):
        UserModel.add_to_class("has_role", has_role)
    if not hasattr(UserModel, 'is_dragon'):
        UserModel.add_to_class("is_dragon", is_dragon)

    logger.info(f"Métodos de roles añadidos al modelo User: {UserModel}")