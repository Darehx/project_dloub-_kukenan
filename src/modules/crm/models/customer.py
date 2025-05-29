# src/modules/crm/models/customer.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

class Customer(models.Model): # Cliente DEL TENANT
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='crm_customers'
    )
    # user_account = models.ForeignKey( # Opcional: si los clientes de los tenants también son usuarios de Kukenan
    #     'core.CustomUser',
    #     on_delete=models.SET_NULL, null=True, blank=True,
    #     related_name='tenant_customer_profiles'
    # )
    first_name = models.CharField(_("First Name"), max_length=100, blank=True)
    last_name = models.CharField(_("Last Name"), max_length=100, blank=True)
    email = models.EmailField(_("Email"), blank=True, null=True) # Podría ser único por tenant
    phone = models.CharField(_("Phone"), max_length=30, null=True, blank=True)
    company_name = models.CharField(_("Company Name"), max_length=150, blank=True, null=True)
    address = models.TextField(_("Address"), null=True, blank=True)
    country = CountryField(_("Country"), blank=True, null=True)
    created_at = models.DateTimeField(_("Creation Date"), auto_now_add=True)
    # Otros campos relevantes para un CRM

    class Meta:
        verbose_name = _("Tenant Customer")
        verbose_name_plural = _("Tenant Customers")
        # unique_together = (('tenant', 'email'),) # Si el email debe ser único por tenant
        ordering = ['tenant', 'company_name', 'last_name']

    def __str__(self):
        display = self.company_name or f"{self.first_name} {self.last_name}".strip()
        return f"{display} (Tenant: {self.tenant.name})"