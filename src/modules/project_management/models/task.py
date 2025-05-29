# src/modules/project_management/models/task.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class Task(models.Model): # Antes Deliverable
    # No necesita FK directa a Tenant, hereda de Project
    project = models.ForeignKey(
        'app_project_management.Project', # Referencia string
        on_delete=models.CASCADE, related_name='tasks'
    )
    title = models.CharField(_("Task Title"), max_length=255) # Sugerencia de campo más común
    description = models.TextField(_("Description"), blank=True, null=True)
    STATUS_CHOICES = [
        ('TODO', _('To Do')), ('IN_PROGRESS', _('In Progress')),
        ('REVIEW', _('In Review')), ('DONE', _('Done')),
    ]
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='TODO', db_index=True)
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    # Asignado a un usuario DEL TENANT
    assignee = models.ForeignKey(
        'core.CustomUser', # Usuario del tenant
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tasks',
        limit_choices_to={'tenant_id': models.F('project__tenant_id')} # Asegurar que el assignee sea del mismo tenant que el proyecto
                                                                     # Esto es más avanzado y puede requerir ajustes.
                                                                     # Una validación en el form/serializer es más simple.
    )
    # file = models.FileField(_("Attachment"), upload_to='tenant_tasks/%Y/%m/', null=True, blank=True)
    # Considerar un modelo separado para adjuntos si pueden ser múltiples.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Tenant Task")
        verbose_name_plural = _("Tenant Tasks")
        ordering = ['project', 'due_date', 'created_at']

    def __str__(self):
        return f"{self.title} (Project: {self.project.name})"

# Opcional: ProjectMember para gestionar quién tiene acceso a qué proyectos del tenant
# class ProjectMember(models.Model):
#     project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
#     user = models.ForeignKey('core.CustomUser', on_delete=models.CASCADE, related_name='project_memberships')
#     ROLE_CHOICES = [('admin', 'Admin'), ('editor', 'Editor'), ('viewer', 'Viewer')]
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='viewer')
#     class Meta:
#         unique_together = ('project', 'user')