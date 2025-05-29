# src/ds_owari/models/employee.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import datetime

class JobPosition(models.Model):
    name = models.CharField(_("Position Name"), max_length=50, unique=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    # permissions = models.JSONField( # Considerar si esto se maneja mejor con el sistema de roles de core
    #     _("Permissions JSON"), default=dict, blank=True,
    #     help_text=_("Specific permissions for this position (JSON structure)")
    # )

    class Meta:
        verbose_name = _("Owari Job Position")
        verbose_name_plural = _("Owari Job Positions")
        ordering = ['name']

    def __str__(self):
        return self.name

class Employee(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, # src.core.CustomUser
        on_delete=models.CASCADE,
        related_name='owari_employee_profile', # related_name específico
        verbose_name=_("User Account")
    )
    hire_date = models.DateField(_("Hire Date"), default=datetime.date.today)
    address = models.TextField(_("Address"), null=True, blank=True)
    salary = models.DecimalField(
        _("Salary"), max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    position = models.ForeignKey(
        JobPosition, # Referencia local dentro de ds_owari
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='employees', verbose_name=_("Position")
    )

    class Meta:
        verbose_name = _("Owari Employee")
        verbose_name_plural = _("Owari Employees")
        ordering = ['user__first_name', 'user__last_name']

    @property
    def is_active(self): # Asume que CustomUser tiene is_active
        return self.user.is_active

    def __str__(self):
        position_name = self.position.name if self.position else _("No position")
        status = _("[ACTIVE]") if self.is_active else _("[INACTIVE]")
        display_name = self.user.get_full_name() or self.user.username
        return f"{display_name} ({position_name}) {status}"