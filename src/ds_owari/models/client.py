# src/ds_owari/models/client.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
# Importar CustomUser desde core
# from src.core.models.user import CustomUser # Si AUTH_USER_MODEL es 'src.core.CustomUser'

class Client(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, # Apuntará a src.core.CustomUser
        on_delete=models.CASCADE,
        related_name='owari_client_profile', # related_name específico
        verbose_name=_("User Account")
    )
    # tenant_link = models.OneToOneField( # Opcional: si un cliente de Owari también es un Tenant en Kukenan
    #     'core.Tenant',
    #     on_delete=models.SET_NULL,
    #     null=True, blank=True,
    #     related_name='owari_linked_client',
    #     verbose_name=_("Linked Kukenan Tenant Account")
    # )
    phone = models.CharField(_("Phone"), max_length=30, null=True, blank=True)
    address = models.TextField(_("Address"), null=True, blank=True)
    date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)
    country = CountryField(_("Country"), blank=True, null=True)
    company_name = models.CharField(
        _("Company Name"), max_length=150, blank=True, null=True
    )
    created_at = models.DateTimeField(_("Creation Date"), auto_now_add=True)
    preferred_contact_method = models.CharField(
        _("Preferred Contact Method"), max_length=20,
        choices=[('email', 'Email'), ('phone', 'Phone'), ('whatsapp', 'WhatsApp'), ('other', 'Other')],
        null=True, blank=True
    )
    brand_guidelines = models.FileField(
        _("Brand Guidelines"), upload_to='owari_clients/brand_guidelines/', # Ruta específica
        null=True, blank=True
    )

    class Meta:
        verbose_name = _("Owari Client")
        verbose_name_plural = _("Owari Clients")
        ordering = ['company_name', 'user__first_name'] # Ajustar según CustomUser

    def __str__(self):
        # Asumiendo que CustomUser tiene get_full_name()
        user_display = self.user.get_full_name() or self.user.username
        display_name = self.company_name or user_display
        return f"{display_name}"