from datetime import timedelta

from .annihilation import event_creator
from .models import DateTimeAnnihilation, AnnihilationEnumContext
from .generalization import generalize_datetime


def event_creator_signal_receiver(sender, instance, created, **kwargs):
    """Creates a signal receiver for save events of
     DateTimeAnnihilation objects.
    For object creating events event_creator() is run on iteration 0.

    Parameters
    ----------
    sender: DateTimeAnnihilation
        The class which will be expected
    instance : DateTimeAnnihilation
        The datetimeannihilation for which an annihilation event should
         be created
    created : boolean
        True if object was created and not just updated
    """
    if created:
        # Check if first reduction is at time offset 0.
        # If true, generalize instantly and start event_creator with iteration 1.
        policy_iteration = instance.annihilation_policy.policy["events"][0]
        if policy_iteration["offset"] == 0:
            instance.dt = generalize_datetime(instance.dt, policy_iteration["reduction"])
            if len(instance.annihilation_policy.policy["events"]) > 1:
                event_creator(instance, iteration=1)
        else:
            event_creator(instance, iteration=0)

        enum_key = instance.annihilation_policy.enumeration_key
        if enum_key is not None:
            # Generalize Datetime to at least one second,
            # to use the microseconds for the enumeration
            instance.dt = generalize_datetime(instance.dt, 1)

            context, created = AnnihilationEnumContext.objects.get_or_create(context_key=enum_key)
            count = context.get_and_increment(instance.annihilation_policy)
            instance.dt = instance.dt + timedelta(microseconds=count)

        instance.save()


def delete_datetime_of_deleted_parent(sender, instance, **kwargs):
    """Deletes all DateTimeAnnihilations in OneToOne Relation with
     the given instance.

        Parameters
        ----------
        sender : Class
            The Class containing OneToOne Relations to DateTimeAnnihilations
        instance : Object
            The Instance containing OneToOne Relations to DateTimeAnnihilations
        """
    print("Signal received!")
    for i in instance._meta.get_fields():
        if type(getattr(instance, i.name)) is DateTimeAnnihilation:
            getattr(instance, i.name).delete()

