# src/core/models/tenant.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class Tenant(models.Model):
    """
    Representa una empresa cliente (Tenant) en el sistema SaaS.
    Cada Tenant tendrá sus propios datos aislados en los módulos.
    """
    name = models.CharField(
        _("Company Name"),
        max_length=255,
        unique=True,
        help_text=_("Official name of the tenant company.")
    )
    # slug = models.SlugField(unique=True, help_text=_("Short unique identifier for URLs, etc.")) # Opcional
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Designates whether this tenant is active and can use the system.")
    )
    # Podrías añadir más campos como:
    # plan = models.ForeignKey('SubscriptionPlan', on_delete=models.SET_NULL, null=True, blank=True)
    # domain = models.CharField(max_length=253, unique=True, null=True, blank=True) # Para subdominios por tenant
    # admin_user = models.ForeignKey( # El primer usuario admin del tenant
    #    settings.AUTH_USER_MODEL, # Se resolverá a CustomUser
    #    on_delete=models.SET_NULL,
    #    null=True, blank=True,
    #    related_name='administered_tenants'
    # )

    class Meta:
        verbose_name = _("Tenant Company")
        verbose_name_plural = _("Tenant Companies")
        ordering = ['name']

    def __str__(self):
        return self.name