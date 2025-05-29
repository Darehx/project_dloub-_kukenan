# src/ds_owari/models/provider.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Provider(models.Model):
    name = models.CharField(_("Provider Name"), max_length=255, unique=True)
    contact_person = models.CharField(_("Contact Person"), max_length=255, null=True, blank=True)
    email = models.EmailField(_("Email"), null=True, blank=True)
    phone = models.CharField(_("Phone"), max_length=30, null=True, blank=True)
    services_provided = models.ManyToManyField(
        'app_ds_owari.ServiceOffering',  # <--- USA 'app_ds_owari'
        blank=True,
        related_name='providers',
        verbose_name=_("Service Offerings Provided")
    )
    rating = models.DecimalField(_("Rating"), max_digits=3, decimal_places=1, default=Decimal('5.0'))
    is_active = models.BooleanField(_("Active"), default=True)
    notes = models.TextField(_("Internal Notes"), blank=True)

    class Meta:
        verbose_name = _("Owari Provider")
        verbose_name_plural = _("Owari Providers")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} {'[ACTIVE]' if self.is_active else '[INACTIVE]'}"
