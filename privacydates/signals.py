from datetime import timedelta

from .vanish import event_creator
from .models import VanishingDateTime, VanishingOrderingContext
from .precision import Precision


def event_creator_signal_receiver(sender, instance, created, **kwargs):
    """Creates a signal receiver for save events of VanishingDateTime objects.
    For object creating events event_creator() is run on iteration 0.

    Parameters
    ----------
    sender: VanishingDateTime
        The class which will be expected
    instance : VanishingDateTime
        The VanishingDateTime for which an vanishing event should
         be created
    created : boolean
        True if object was created and not just updated
    """
    del sender  # not used
    if created:
        # Check if first reduction is at time offset 0.
        # If true, roughen instantly and start event_creator with iteration 1.
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
    """Deletes all VanishingDateTime in OneToOne Relation with the given instance.

    Parameters
    ----------
    sender : Class
        The Class containing OneToOne Relations to DateTimeAnnihilations
    instance : Object
        The Instance containing OneToOne Relations to DateTimeAnnihilations
    """
    for field in instance._meta.get_fields():
        if isinstance(getattr(instance, field.name), VanishingDateTime):
            getattr(instance, field.name).delete()
