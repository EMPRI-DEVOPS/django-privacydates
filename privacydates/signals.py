"""Signals for maintaining vanishing dates"""
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .vanish import event_creator
from .models import VanishingDateTime, VanishingOrderingContext
from .precision import Precision


@receiver(post_save, sender=VanishingDateTime)
@transaction.atomic
def create_initial_vanishing_event(sender, instance, created, **kwargs):
    """Create initial VanishingEvent for newly saved vanishing dates"""
    if not created:
        return  # no nothing

    # Check if first precision should be applied immediately
    # If so, do and start event_creator with iteration 1.
    first_precision: Precision = instance.vanishing_policy.policy[0]
    if first_precision.is_applied_immediately():
        instance.dt = first_precision.apply(instance.dt)
        if len(instance.vanishing_policy.policy) > 1:
            event_creator(instance, iteration=1)
    else:
        event_creator(instance, iteration=0)

    enum_key = instance.vanishing_policy.ordering_key
    if enum_key is not None:
        # Use microseconds for ordering.
        context, _ = VanishingOrderingContext.objects.get_or_create(context_key=enum_key)
        count = context.get_and_increment(instance.vanishing_policy)
        instance.dt = instance.dt.replace(microsecond=count)
    instance.save()


def delete_datetime_of_deleted_parent(sender, instance, **kwargs):
    """Delete all VanishingDateTime in relation with the given instance"""
    for field in instance._meta.get_fields():
        if isinstance(getattr(instance, field.name), VanishingDateTime):
            getattr(instance, field.name).delete()
