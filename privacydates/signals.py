from datetime import timedelta

from .vanish import event_creator
from .models import VanishingDateTime, VanishingOrderingContext
from .rough import roughen_datetime


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
    if created:
        # Check if first reduction is at time offset 0.
        # If true, roughen instantly and start event_creator with iteration 1.
        policy_iteration = instance.vanishing_policy.policy["events"][0]
        if policy_iteration["offset"] == 0:
            instance.dt = roughen_datetime(instance.dt, policy_iteration["reduction"])
            if len(instance.vanishing_policy.policy["events"]) > 1:
                event_creator(instance, iteration=1)
        else:
            event_creator(instance, iteration=0)

        enum_key = instance.vanishing_policy.ordering_key
        if enum_key is not None:
            # Roughen Datetime to at least one second,
            # to use the microseconds for the ordering.
            instance.dt = roughen_datetime(instance.dt, 1)

            context, created = VanishingOrderingContext.objects.get_or_create(context_key=enum_key)
            count = context.get_and_increment(instance.vanishing_policy)
            instance.dt = instance.dt + timedelta(microseconds=count)

        instance.save()


def delete_datetime_of_deleted_parent(sender, instance, **kwargs):
    """Deletes all VanishingDateTime which are linked by a ForeignKey with the given instance.

        Parameters
        ----------
        sender : Class
            The Class containing ForeignKey Relations to DateTimeAnnihilations
        instance : Object
            The Instance containing ForeignKey Relations to DateTimeAnnihilations
        """
    for i in instance._meta.get_fields():
        if type(getattr(instance, i.name)) is VanishingDateTime:
            getattr(instance, i.name).delete()

