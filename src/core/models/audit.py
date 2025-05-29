# src/core/models/audit.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class AuditLog(models.Model):
    """Registro de auditoría de acciones importantes."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Se resolverá a 'core.CustomUser'
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_("User")
    )
    # Opcional: Si las acciones de auditoría son específicas del tenant
    # tenant = models.ForeignKey(
    #    'core.Tenant',
    #    on_delete=models.SET_NULL, # O CASCADE
    #    null=True, blank=True,
    #    related_name='audit_logs'
    # )
    action = models.CharField(
        _("Action"),
        max_length=255,
        help_text=_("Description of the action performed")
    )
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True, db_index=True)
    
    # Para identificar el objeto afectado
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Content Type")
    )
    object_id = models.PositiveIntegerField(
        _("Object ID"),
        null=True, blank=True
    )
    object_repr = models.CharField(
        _("Object Representation"),
        max_length=200,
        blank=True
    )
    # from django.contrib.contenttypes.fields import GenericForeignKey
    # content_object = GenericForeignKey('content_type', 'object_id') # Si quieres una relación genérica directa

    details = models.JSONField(
        _("Details"),
        default=dict,
        blank=True,
        help_text=_("Additional details in JSON format (e.g., changed fields)")
    )
    ip_address = models.GenericIPAddressField(
        _("IP Address"),
        null=True, blank=True
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")

    def __str__(self):
        user_str = self.user.get_username() if self.user else _("System")
        timestamp_str = self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else 'N/A'
        return f"{timestamp_str} - {user_str}: {self.action}"

    @property
    def target(self):
        """Devuelve el objeto real al que se refiere el log, si es posible."""
        if self.content_type and self.object_id:
            try:
                return self.content_type.get_object_for_this_type(pk=self.object_id)
            except self.content_type.model_class().DoesNotExist:
                return None
        return None