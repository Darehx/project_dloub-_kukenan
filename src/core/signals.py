# src/core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile # Importa UserProfile de core.models

@receiver(post_save, sender=settings.AUTH_USER_MODEL) # Escucha a CustomUser
def create_user_profile_on_user_creation(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)