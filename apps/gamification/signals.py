"""
Signals for Gamification app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserGamification

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_gamification(sender, instance, created, **kwargs):
    """Create UserGamification when a new User is created."""
    if created:
        UserGamification.objects.get_or_create(user=instance)
