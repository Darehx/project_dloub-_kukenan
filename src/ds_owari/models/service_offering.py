# src/ds_owari/models/service_offering.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import datetime
# from .campaign import Campaign # No necesitas este import si usas referencia string

class OfferingCategory(models.Model): # Antes ServiceCategory
    code = models.CharField(_("Category Code"), max_length=10, primary_key=True)
    name = models.CharField(_("Category Name"), max_length=100)

    class Meta:
        verbose_name = _("Owari Service Offering Category")
        verbose_name_plural = _("Owari Service Offering Categories")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class ServiceOffering(models.Model): # Antes Service
    code = models.CharField(_("Offering Code"), max_length=10, primary_key=True)
    category = models.ForeignKey(
        OfferingCategory, # Referencia local directa (modelo en el mismo archivo o importado arriba)
        on_delete=models.PROTECT, related_name='service_offerings'
    )
    name = models.CharField(_("Offering Name"), max_length=255)
    is_active = models.BooleanField(_("Active"), default=True)
    # ventulab = models.BooleanField(_("Ventulab"), default=False)

    campaign = models.ForeignKey(
        'app_ds_owari.Campaign', # <--- CORRECCIÓN: Usa la label 'app_ds_owari'
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='promoted_offerings', verbose_name=_("Associated Campaign")
    )

    is_package = models.BooleanField(_("Is Package"), default=False)
    is_subscription = models.BooleanField(_("Is Subscription"), default=False)
    audience = models.TextField(_("Target Audience"), blank=True, null=True)
    detailed_description = models.TextField(_("Detailed Description"), blank=True, null=True)
    problem_solved = models.TextField(_("Problem Solved"), blank=True, null=True)

    class Meta:
        verbose_name = _("Owari Service Offering")
        verbose_name_plural = _("Owari Service Offerings")
        ordering = ['category', 'name']

    def __str__(self):
        # Ajusta según los nombres de campo reales y si son opcionales
        package_indicator = _(" [Paquete]") if self.is_package else ""
        subscription_indicator = _(" [Suscripción]") if self.is_subscription else ""
        status_indicator = _("[ACTIVO]") if self.is_active else _("[INACTIVO]") # Ejemplo
        return f"{self.name} ({self.code}){package_indicator}{subscription_indicator} {status_indicator}"


    def get_current_price(self, currency='EUR'):
        if hasattr(self, 'price_history'): # Chequeo defensivo
            latest_price = self.price_history.filter(currency=currency).order_by('-effective_date').first()
            return latest_price.amount if latest_price else None
        return None


class OfferingFeature(models.Model): # Antes ServiceFeature
    FEATURE_TYPES = [
        ('differentiator', _('Differentiator')), ('benefit', _('Benefit')),
        ('characteristic', _('Characteristic')), ('process', _('Process')),
        ('expected_result', _('Expected Result')),
    ]
    service_offering = models.ForeignKey(
        ServiceOffering, # Referencia local directa
        on_delete=models.CASCADE, related_name='features'
    )
    feature_type = models.CharField(_("Type"), max_length=20, choices=FEATURE_TYPES)
    description = models.TextField(_("Description"))

    class Meta:
        verbose_name = _("Owari Offering Feature")
        verbose_name_plural = _("Owari Offering Features")
        ordering = ['service_offering', 'feature_type']

    def __str__(self):
        service_code = self.service_offering.code if hasattr(self.service_offering, 'code') else "N/A"
        return f"{service_code} - {self.get_feature_type_display()}"


class OfferingPrice(models.Model): # Antes Price
    service_offering = models.ForeignKey(
        ServiceOffering, # Referencia local directa
        on_delete=models.CASCADE, related_name='price_history'
    )
    amount = models.DecimalField(_("Amount"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=3, default='EUR')
    effective_date = models.DateField(_("Effective Date"), default=datetime.date.today)

    class Meta:
        verbose_name = _("Owari Offering Price")
        verbose_name_plural = _("Owari Offering Price History")
        get_latest_by = 'effective_date'
        ordering = ['service_offering', 'currency', '-effective_date']
        unique_together = ['service_offering', 'currency', 'effective_date']

    def __str__(self):
        service_code = self.service_offering.code if hasattr(self.service_offering, 'code') else "N/A"
        return f"Price of {service_code} - {self.amount} {self.currency}"