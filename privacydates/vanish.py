from warnings import warn
import datetime
from django.utils import timezone

from .models import VanishingEvent, VanishingDateTime, VanishingPolicy
from .rough import roughen_datetime


def event_creator(instance: VanishingDateTime, iteration: int) -> None:
    """Creates a Annihilation event for a given instance of
    DateTimeAnnihilation

    Parameters
    ----------
    instance : VanishingDateTime
        The VanishingDateTime for which an vanishing event should
         be created
    iteration : int
        The Vanishing iteration the event should use of the
         VanishingPolicy

    """
    policy_iteration = instance.vanishing_policy.policy["events"][iteration]
    event_date = instance.dt + datetime.timedelta(minutes=policy_iteration["offset"])

    ae = VanishingEvent(vanishing_datetime=instance,
                        event_date=event_date,
                        iteration=iteration)
    ae.save()


def vanishing_updater():
    """Executes all pending vanishing events registered by
     an VanishingEvent.
    This includes changing the timestamps and creating a new
     VanishingEvents when specified.

    """
    events_pending = True
    while events_pending:
        # Get all vanishing events
        ae_list = VanishingEvent.objects.all()
        events_pending = False
        now = timezone.now()
        for ae in ae_list:
            if ae is not None and ae.event_date <= now:
                # Set events_pending to true,
                # as a newly created vanishing event may already be in the past,
                # and a new iteration over events is necessary.
                events_pending = True
                # Save Ordering
                order_count = int(ae.vanishing_datetime.dt.strftime('%f'))
                # Generalize Datetime
                ae.vanishing_datetime.dt = roughen_datetime(
                    ae.vanishing_datetime.dt,
                    ae.vanishing_datetime.vanishing_policy.
                    policy["events"][ae.iteration]["reduction"])
                # Re add Order, if Ordering functionality was used.
                if ae.vanishing_datetime.vanishing_policy.ordering_key is not None:
                    ae.vanishing_datetime.dt = (ae.vanishing_datetime.dt
                                                + datetime.timedelta(microseconds=order_count))

                ae.vanishing_datetime.save()
                # Create next event, if applicable
                iteration = ae.iteration + 1
                if iteration < len(ae.vanishing_datetime.vanishing_policy.policy["events"]):
                    event_creator(ae.vanishing_datetime, iteration=iteration)
                # Delete old event
                ae.delete()


def vanishingdatetime_creator(
        dt: datetime.datetime,
        vanishing_policy: VanishingPolicy,
) -> VanishingDateTime:
    """Creates and saves a VanishingDateTime object with the given
     datetime and VanishingPolicy

        Parameters
        ----------
        dt : datetime.datetime
            The datetime which  the VanishingDateTime instance
             should be initialised.

        vanishing_policy : VanishingPolicy
            The VanishingPolicy assigned to the VanishingDateTime
             instance.

        Returns
        -------
        VanishingDateTime
            Created and saved VanishingDateTime instance
        """
    dta = VanishingDateTime(dt=dt, vanishing_policy=vanishing_policy)
    dta.save()
    return dta


def make_policy(policy, ordering_key=None):
    """Creates or Gets (when already existing) an VanishingPolicy
     with the given dict and return the created object

    Parameters
    ----------
    policy : dict
        dict containing the planned vanishing events with
         the following format:

        "events": [
            {
                "offset" : 1,
                "reduction" : 20
            },
            {
                "offset" : 3,
                "reduction" : 60
            }
        ],

       The dict must be sorted by ascending offset.

    ordering_key : string
        string containing the unique key for vanishing context.
         (Optional)

    Returns
    -------
    VanishingPolicy
        The created Policy
    """
    ap, created = VanishingPolicy.objects.get_or_create(policy=policy,
                                                        ordering_key=ordering_key)
    if created:
        if "events" not in policy:
            raise ValueError('no list "events" in policy dict for AnnihilationPolicy')
        if not policy["events"]:
            raise ValueError('list "events" is empty')
        for event in policy["events"]:
            if "offset" not in event or "reduction" not in event:
                raise ValueError('An entry in "events" has a wrong format')

        # Check if the offset is ascending, Give Warning otherwise
        tmp_offset = -1
        for event in policy["events"]:
            if not event["offset"] > tmp_offset:
                warn("Events of AnnihilationPolicy are not sorted by offset")
            tmp_offset = event["offset"]
    return ap
