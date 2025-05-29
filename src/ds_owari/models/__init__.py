# src/ds_owari/models/__init__.py
from .client import Client
from .employee import JobPosition, Employee
from .service_offering import OfferingCategory, ServiceOffering, OfferingFeature, OfferingPrice
from .campaign import Campaign, CampaignServiceOffering
from .order import InternalOrder, InternalOrderServiceLine, InternalTask # LÍNEA CORREGIDA
from .internal_finance import InternalInvoice, InternalPayment
from .provider import Provider

__all__ = [
    'Client', 'JobPosition', 'Employee',
    'OfferingCategory', 'ServiceOffering', 'OfferingFeature', 'OfferingPrice',
    'Campaign', 'CampaignServiceOffering',
    'InternalOrder', 'InternalOrderServiceLine', 'InternalTask', # ASEGÚRATE DE QUE ESTÉN AQUÍ CON LOS NOMBRES CORRECTOS
    'InternalInvoice', 'InternalPayment',
    'Provider',
]