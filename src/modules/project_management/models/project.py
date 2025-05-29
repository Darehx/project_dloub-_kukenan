# src/modules/project_management/models/project.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
# from decimal import Decimal # Si los proyectos tienen montos directos

class Project(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='projects'
    )
    name = models.CharField(_("Project Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True, null=True)
    # Referencia al cliente del Tenant, si aplica
    # customer = models.ForeignKey(
    #     'modules_crm.Customer',
    #     on_delete=models.SET_NULL, null=True, blank=True,
    #     related_name='projects'
    # )
    STATUS_CHOICES = [
        ('PLANNING', _('Planning')), ('IN_PROGRESS', _('In Progress')),
        ('ON_HOLD', _('On Hold')), ('COMPLETED', _('Completed')),
        ('CANCELLED', _('Cancelled')),
    ]
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='PLANNING', db_index=True)
    start_date = models.DateField(_("Start Date"), null=True, blank=True)
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completion Date"), null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Tenant Project")
        verbose_name_plural = _("Tenant Projects")
        ordering = ['tenant', '-created_at']

    def __str__(self):
        return f"{self.name} (Tenant: {self.tenant.name})"

    # Lógica para `completed_at` similar a la de Order original
    def save(self, *args, **kwargs):
        if self.status == 'COMPLETED' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'COMPLETED' and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)