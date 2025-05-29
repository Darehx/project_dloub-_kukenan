# src/core/models/notification.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Notification(models.Model):
    """Notificaciones para usuarios."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Se resolverá a 'core.CustomUser'
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_("User")
    )
    # Opcional: Si las notificaciones son específicas del tenant
    # tenant = models.ForeignKey(
    #    'core.Tenant',
    #    on_delete=models.CASCADE, # Si el tenant se borra, sus notificaciones también
    #    null=True, blank=True, # Si algunas notificaciones son globales
    #    related_name='notifications'
    # )
    message = models.TextField(_("Message"))
    read = models.BooleanField(_("Read"), default=False, db_index=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    link = models.URLField(
        _("Link"),
        null=True, blank=True,
        help_text=_("Relevant link (e.g., to an order, task)")
    )
    # Opcional: Tipo de notificación para filtrado o iconos
    # NOTIFICATION_TYPES = [('info', 'Information'), ('alert', 'Alert'), ('task', 'Task Update')]
    # notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='info')

    # Opcional: Para notificaciones relacionadas con un objeto específico
    # content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, null=True, blank=True)
    # object_id = models.PositiveIntegerField(null=True, blank=True)
    # from django.contrib.contenttypes.fields import GenericForeignKey
    # content_object = GenericForeignKey('content_type', 'object_id')


    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")

    def __str__(self):
        status = _("[Read]") if self.read else _("[Unread]")
        username = self.user.get_username() if hasattr(self, 'user') else 'N/A'
        return f"Notification for {username} {status}: {self.message[:50]}..."

    def mark_as_read(self):
        if not self.read:
            self.read = True
            self.save(update_fields=['read'])

    def mark_as_unread(self):
        if self.read:
            self.read = False
            self.save(update_fields=['read'])