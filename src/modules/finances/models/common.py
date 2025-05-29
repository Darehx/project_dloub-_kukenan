# src/modules/finances/models/common.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class TransactionType(models.Model):
    """
    Tipos de transacciones financieras.
    Estos pueden ser globales (definidos por la plataforma) o específicos del tenant.
    """
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='transaction_types',
        null=True, # True si puede haber tipos globales no asociados a un tenant
        blank=True,
        verbose_name=_("Tenant")
    )
    name = models.CharField(
        _("Transaction Type Name"),
        max_length=100 # Aumentado para nombres más descriptivos
    )
    description = models.TextField(_("Description"), blank=True, null=True)
    # Por ejemplo: 'income', 'expense', 'refund', 'internal_transfer'
    # Esto podría ayudar a categorizar y generar reportes.
    category = models.CharField(
        _("Category"),
        max_length=50,
        choices=[
            ('income', _('Income')),
            ('expense', _('Expense')),
            ('refund_out', _('Refund Issued')), # Reembolso que el tenant hace
            ('refund_in', _('Refund Received')), # Reembolso que el tenant recibe
            ('internal', _('Internal Transfer')),
            ('other', _('Other')),
        ],
        blank=True, null=True
    )
    requires_approval = models.BooleanField(_("Requires Approval"), default=False)
    is_global = models.BooleanField(
        _("Is Global Type"),
        default=False,
        help_text=_("If true, this type is available to all tenants or for platform use.")
    )
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("Transaction Type")
        verbose_name_plural = _("Transaction Types")
        unique_together = (('tenant', 'name'),) # El nombre debe ser único por tenant, o global si tenant es NULL
        ordering = ['name']

    def __str__(self):
        if self.is_global:
            return f"{self.name} (Global)"
        elif self.tenant:
            return f"{self.name} (Tenant: {self.tenant.name})"
        return self.name

class PaymentMethod(models.Model):
    """
    Métodos de pago.
    Estos pueden ser globales o específicos del tenant.
    """
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='payment_methods',
        null=True, # True si puede haber métodos globales
        blank=True,
        verbose_name=_("Tenant")
    )
    name = models.CharField(
        _("Payment Method Name"),
        max_length=100 # Aumentado
    )
    # Por ejemplo: 'bank_transfer', 'credit_card', 'paypal', 'cash', 'check'
    type_code = models.CharField(
        _("Type Code"),
        max_length=50,
        blank=True, null=True,
        help_text=_("An internal code for the payment method type.")
    )
    description = models.TextField(_("Description"), blank=True, null=True)
    is_global = models.BooleanField(
        _("Is Global Method"),
        default=False,
        help_text=_("If true, this method is available to all tenants or for platform use.")
    )
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Payment Method")
        verbose_name_plural = _("Payment Methods")
        unique_together = (('tenant', 'name'),) # El nombre debe ser único por tenant, o global si tenant es NULL
        ordering = ['name']

    def __str__(self):
        status = '' if self.is_active else _(' (Inactive)')
        if self.is_global:
            return f"{self.name} (Global){status}"
        elif self.tenant:
            return f"{self.name} (Tenant: {self.tenant.name}){status}"
        return f"{self.name}{status}"