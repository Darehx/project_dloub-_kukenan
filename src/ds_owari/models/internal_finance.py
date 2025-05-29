# src/ds_owari/models/internal_finance.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import datetime

class InternalInvoice(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('SENT', _('Sent')),
        ('PAID', _('Paid')),
        ('PARTIALLY_PAID', _('Partially Paid')),
        ('OVERDUE', _('Overdue')),
        ('CANCELLED', _('Cancelled')),
        ('VOID', _('Void')),
    ]
    FINAL_STATUSES = ['PAID', 'CANCELLED', 'VOID']

    order = models.ForeignKey(
        'app_ds_owari.InternalOrder', # Usa la label de DsOwariConfig
        on_delete=models.PROTECT,
        related_name='internal_invoices'
    )
    invoice_number = models.CharField(
        _("Invoice Number"),
        max_length=50,
        unique=True,
        blank=True
    )
    date = models.DateField(_("Issue Date"), default=datetime.date.today)
    due_date = models.DateField(_("Due Date"))
    paid_amount = models.DecimalField(
        _("Amount Paid"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True
    )
    notes = models.TextField(_("Notes/Terms"), blank=True)

    class Meta:
        verbose_name = _("Owari Internal Invoice")
        verbose_name_plural = _("Owari Internal Invoices")
        ordering = ['-date', '-id']

    @property
    def total_amount(self):
        return self.order.total_amount if self.order and hasattr(self.order, 'total_amount') else Decimal('0.00')

    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount

    def __str__(self):
        client_name = self.order.client if self.order and hasattr(self.order, 'client') else _("Unknown Client")
        return f"Internal Invoice {self.invoice_number} for {client_name}"


class InternalPayment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('COMPLETED', _('Completed')),
        ('FAILED', _('Failed')),
        ('REFUNDED', _('Refunded')),
    ]

    invoice = models.ForeignKey(
        InternalInvoice, # Referencia directa al modelo en el mismo archivo
        on_delete=models.CASCADE,
        related_name='internal_payments'
    )
    method = models.ForeignKey(
        'app_finances.PaymentMethod', # CORREGIDO: Usa la label de FinancesConfig
        on_delete=models.PROTECT,
        verbose_name=_("Payment Method")
    )
    transaction_type = models.ForeignKey(
        'app_finances.TransactionType', # CORREGIDO: Usa la label de FinancesConfig
        on_delete=models.PROTECT,
        verbose_name=_("Transaction Type")
    )
    date = models.DateTimeField(_("Payment Date"), default=timezone.now)
    amount = models.DecimalField(_("Amount"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=3, default='EUR')
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='COMPLETED',
        db_index=True
    )
    transaction_id = models.CharField(
        _("External Transaction ID"),
        max_length=100,
        blank=True,
        null=True
    )
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Owari Internal Payment")
        verbose_name_plural = _("Owari Internal Payments")
        ordering = ['-date']

    def __str__(self):
        invoice_num = self.invoice.invoice_number if self.invoice else _("N/A")
        return f"Internal Payment {self.amount} {self.currency} for Invoice {invoice_num}"