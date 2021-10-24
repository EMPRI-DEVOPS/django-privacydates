from warnings import warn
import datetime
from django.utils import timezone

from .models import AnnihilationEvent, DateTimeAnnihilation, AnnihilationPolicy
from .generalization import generalize_datetime


def event_creator(instance: DateTimeAnnihilation, iteration: int) -> None:
    """Creates a Annihilation event for a given instance of
    DateTimeAnnihilation

    Parameters
    ----------
    instance : DateTimeAnnihilation
        The datetimeannihilation for which an annihilation event should
         be created
    iteration : int
        The Annihilation iteration the event should use of the
         AnnihilationPolicy

    """
    policy_iteration = instance.annihilation_policy.policy["events"][iteration]
    event_date = instance.dt + datetime.timedelta(minutes=policy_iteration["offset"])

    ae = AnnihilationEvent(datetime_annihilation=instance,
                           event_date=event_date,
                           iteration=iteration)
    ae.save()


def annihilation_updater():
    """Executes all pending annihilations registered by
     an AnnihilationEvent.
    This includes changing the timestamps and creating a new
     AnnihilationEvents when specified.

    """
    events_pending = True
    while events_pending:
        # Get all annihilation events
        ae_list = AnnihilationEvent.objects.all()
        events_pending = False
        for ae in ae_list:
            if ae is not None and ae.event_date < timezone.now():
                # Set events_pending to true,
                # as a newly created annihilation event may already be in the past,
                # and a new iteration over events is necessary.
                events_pending = True
                # Save enumeration
                enum_count = int(ae.datetime_annihilation.dt.strftime('%f'))
                # Generalize Datetime
                ae.datetime_annihilation.dt = generalize_datetime(
                    ae.datetime_annihilation.dt,
                    ae.datetime_annihilation.annihilation_policy.
                    policy["events"][ae.iteration]["reduction"])
                # Re add enumeration, if enumeration functionality was used.
                if ae.datetime_annihilation.annihilation_policy.enumeration_key is not None:
                    ae.datetime_annihilation.dt = (ae.datetime_annihilation.dt
                                                   + datetime.timedelta(microseconds=enum_count))

                ae.datetime_annihilation.save()
                # Create next event, if applicable
                iteration = ae.iteration + 1
                if iteration < len(ae.datetime_annihilation.annihilation_policy.policy["events"]):
                    event_creator(ae.datetime_annihilation, iteration=iteration)
                # Delete old event
                ae.delete()


def datetimeannihilation_creator(
        dt: datetime.datetime,
        annihilation_policy: AnnihilationPolicy,
) -> DateTimeAnnihilation:
    """Creates and saves an DateTimeAnnihilation object with the given
     datetime and annihilationpolicy

        Parameters
        ----------
        dt : datetime.datetime
            The datetime which  the DateTimeAnnihilation instance
             should be initialised.

        annihilation_policy : AnnihilationPolicy
            The AnnihilationPolicy assigned to the DateTimeAnnihilation
             instance.

        Returns
        -------
        DateTimeAnnihilation
            Created and saved DateTimeAnnihilation instance
        """
    dta = DateTimeAnnihilation(dt=dt, annihilation_policy=annihilation_policy)
    dta.save()
    return dta


def annihilation_policy_creator(policy, enumeration_key=None):
    """Creates or Gets (when already existing) an AnnihilationPolicy
     with the given dict and return the created object

    Parameters
    ----------
    policy : dict
        dict containing the planned annihilations with
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

    enumeration_key : string
        string containing the unique key for enumeration context.
         (Optional)

    Returns
    -------
    AnnihilationPolicy
        The created Policy
    """
    ap, created = AnnihilationPolicy.objects.get_or_create(policy=policy,
                                                           enumeration_key=enumeration_key)
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
