# src/modules/crm/models/form.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class Form(models.Model):
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='crm_forms'
    )
    name = models.CharField(_("Form Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    created_at = models.DateTimeField(_("Creation Date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Tenant Form")
        verbose_name_plural = _("Tenant Forms")
        ordering = ['tenant', 'name']

    def __str__(self):
        return f"{self.name} (Tenant: {self.tenant.name})"

class FormQuestion(models.Model):
    # No necesita FK directa a Tenant, hereda de Form
    form = models.ForeignKey(
        Form, # Referencia local
        on_delete=models.CASCADE, related_name='questions'
    )
    question_text = models.TextField(_("Question Text"))
    order = models.PositiveIntegerField(_("Order"), default=0)
    required = models.BooleanField(_("Required"), default=True)

    class Meta:
        verbose_name = _("Tenant Form Question")
        verbose_name_plural = _("Tenant Form Questions")
        ordering = ['form', 'order']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}... (Form: {self.form.name})"


class FormResponse(models.Model):
    # No necesita FK directa a Tenant, hereda de Form y Question (y Customer si es del Tenant)
    form = models.ForeignKey(
        Form, # Referencia local
        on_delete=models.CASCADE, related_name='responses'
    )
    question = models.ForeignKey(
        FormQuestion, # Referencia local
        on_delete=models.CASCADE, related_name='responses'
    )
    # Asumimos que la respuesta es de un Customer DEL TENANT
    customer = models.ForeignKey(
        'app_crm.Customer', # Referencia string al Customer de este módulo
        on_delete=models.CASCADE,
        related_name='form_responses',
        verbose_name=_("Responding Customer")
    )
    text = models.TextField(_("Response Text"))
    created_at = models.DateTimeField(_("Response Date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Tenant Form Response")
        verbose_name_plural = _("Tenant Form Responses")
        # unique_together = ('customer', 'form', 'question') # Considerar si esto aplica
        ordering = ['created_at']

    def __str__(self):
        return f"Response by {self.customer} to Q: {self.question.question_text[:20]}..."