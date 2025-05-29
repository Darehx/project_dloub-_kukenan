# src/ds_owari/models/campaign.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

class Campaign(models.Model):
    campaign_code = models.CharField(_("Campaign Code"), max_length=20, primary_key=True)
    campaign_name = models.CharField(_("Campaign Name"), max_length=255)
    start_date = models.DateTimeField(_("Start Date"))
    end_date = models.DateTimeField(_("End Date"), null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    target_audience = models.JSONField(_("Target Audience"), default=dict, blank=True)
    budget = models.DecimalField(_("Budget"), max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Owari Campaign")
        verbose_name_plural = _("Owari Campaigns")
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.campaign_name} ({self.campaign_code})"
    
# src/ds_owari/models/campaign.py
# ... (otros imports y la clase Campaign) ...

class CampaignServiceOffering(models.Model):
    campaign = models.ForeignKey(
        'app_ds_owari.Campaign',
        on_delete=models.CASCADE,
        related_name='included_offerings'
    )
    service_offering = models.ForeignKey(
        'app_ds_owari.ServiceOffering',
        on_delete=models.CASCADE,
        related_name='campaign_assignments'
    )
    # ASEGÚRATE DE QUE ESTA SECCIÓN ESTÉ EXACTAMENTE ASÍ:
    discount_percentage = models.DecimalField( # Comienzo de la línea 35 o cercana
        _("Discount (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    ) # Fin del campo
    additional_details = models.TextField(
        _("Additional Details"),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Owari Campaign Service Offering")
        verbose_name_plural = _("Owari Campaign Service Offerings")
        unique_together = ('campaign', 'service_offering')

    def __str__(self):
        service_offering_name = self.service_offering.name if hasattr(self, 'service_offering') and self.service_offering else "N/A"
        campaign_name = self.campaign.campaign_name if hasattr(self, 'campaign') and self.campaign else "N/A"
        return f"{service_offering_name} in campaign {campaign_name}"