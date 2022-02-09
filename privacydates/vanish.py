"""Uitilites for VanishingDateField"""
from datetime import datetime, timedelta
from typing import List, Optional, overload

from django.db import transaction
from django.utils import timezone

from .models import VanishingEvent, VanishingDateTime, VanishingPolicy
from .order import hash_context_key
from .precision import Precision


__all__ = [
    'VanishingFactory', 'update_vanishing',
]


PolicySteps = List[Precision]


def event_creator(instance: VanishingDateTime, iteration: int) -> None:
    """Create a vanishing event for a given instance of VanishingDateTime

    Parameters
    ----------
    instance : VanishingDateTime
        The VanishingDateTime for which the event should be created
    iteration : int
        The iteration step in the VanishingPolicy
    """
    next_precision: Precision = instance.vanishing_policy.policy[iteration]
    assert next_precision.apply_after_seconds is not None
    event_date = instance.dt + next_precision.apply_after_timedelta
    VanishingEvent.objects.create(
        vanishing_datetime=instance,
        event_date=event_date,
        iteration=iteration,
    )


def update_vanishing():
    """Executes all pending vanishing events.
    This includes changing the timestamps and creating succeding
    VanishingEvents if necessary.
    """
    now = timezone.now()
    events_pending = True
    while events_pending:
        events_pending = False
        for event in VanishingEvent.objects.filter(event_date__lte=now):
            # Set events_pending to true,
            # as a newly created vanishing event may already be in the past,
            # and a new iteration over events is necessary.
            events_pending = True
            execute_event(event)


@transaction.atomic()
def execute_event(event: VanishingEvent):
    """Execute vanishing event."""
    # Save ordering
    vandate = event.vanishing_datetime
    order_count = int(vandate.dt.strftime('%f'))
    # Generalize Datetime
    policy = vandate.vanishing_policy.policy
    new_precision = policy[event.iteration]
    vandate.dt = new_precision.apply(vandate.dt)
    # Re-add order, if ordering functionality was used.
    if vandate.vanishing_policy.ordering_key:
        vandate.dt += timedelta(microseconds=order_count)
    vandate.save()
    # Create next event, if more step are planned
    next_iteration = event.iteration + 1
    if next_iteration < len(event.vanishing_datetime.vanishing_policy.policy):
        event_creator(vandate, iteration=next_iteration)
    event.delete()  ## Delete old event


class VanishingFactory:
    """Factory for creating VanishingDateTime instances assignable to
    VanishingDateFields.
    """

    @overload
    def __init__(self, policy: Optional[VanishingPolicy] = None):
        ...
    @overload
    def __init__(self, policy: Optional[PolicySteps] = None,
                 context: Optional[str] = None,
                 hashed=False):
        ...
    def __init__(self, policy=None, context=None, hashed=False):
        """Setup factory for VanishingDateTime instances.
        A policy can be provided to use for all dates.

        Parameters
        ----------
        date : datetime
            The initial datetime

        policy : VanishingPolicy or list of Precision (optional)
            VanishingPolicy or list of policy steps to be used for this date

        context : str (optional)
            Context key used for deteriming this dates ordering context

        hashed : bool (default: False)
            Flag to indicate whether the context key should be hashed with
            SHA256 before storing.
        """
        self._policy_obj = None
        self._policy_list = None
        self._context = None
        if isinstance(policy, list):
            self._policy_list = policy
            if context and hashed:
                context = hash_context_key(context)
            self._context = context
        elif isinstance(policy, VanishingPolicy):
            self._policy_obj = policy
            if context:
                raise ValueError("No context allowed for VanishingPolicy type")
        elif policy is None:
            # setup factory without default policy
            if context:
                raise ValueError("No context allowed without policy")
        else:
            raise TypeError("Unexpected policy type")

    @property
    def policy(self) -> Optional[VanishingPolicy]:
        """This will lazily create a VanishingPolicy if policy steps were given
        to init."""
        # Laziness prevents creation of policy objects that never were used for
        # creating vanishing dates.
        if not self._policy_obj:
            if not self._policy_list:
                return None
            self._policy_obj = make_policy(self._policy_list, self._context)
        return self._policy_obj


    @overload
    def create(self, date: datetime,
               policy: Optional[VanishingPolicy] = None) -> VanishingDateTime:
        ...
    @overload
    def create(self, date: datetime,
               policy: Optional[PolicySteps] = None,
               context: Optional[str] = None,
               hashed=False) -> VanishingDateTime:
        ...
    def create(self, date, policy=None, context=None, hashed=False):
        """Creates and saves a VanishingDateTime object with the given
        datetime.
        A policy and/or context can be provided to use instead of the factory's
        policy. If a context but no policy is provided, a new policy object
        will be created combining the factory's policy and the given context.

        Parameters
        ----------
        date : datetime
            The initial datetime

        policy : VanishingPolicy or list of Precision (optional)
            VanishingPolicy or list of policy steps to be used for this date

        context : str (optional)
            Context key used for deteriming this dates ordering context

        hashed : bool (default: False)
            Flag to indicate whether the context key should be hashed with
            SHA256 before storing.

        Returns
        -------
        VanishingDateTime
        """
        if not policy and not self.policy:
            raise ValueError("No policy provided")
        if hashed and context:
            context = hash_context_key(context)
        if isinstance(policy, list):
            policy = make_policy(policy, context)
        if context and not policy:
            # create new VanishingPolicy reusing the global policy but with the
            # given context key
            policy = make_policy(self.policy.policy, context)
        if not policy:
            policy = self.policy
        vandate = VanishingDateTime(dt=date, vanishing_policy=policy)
        vandate.save()
        return vandate


def validate_policy(policy: PolicySteps):
    """Validate correct order of policy steps"""
    if not policy:
        raise ValueError("Empty policy")
    num_instant = sum(1 for step in policy if step.apply_after_seconds is None)
    if num_instant > 1:
        raise ValueError("Multiple steps without delay")
    prev = policy[0]
    if num_instant == 1 and prev.apply_after_seconds:
        raise ValueError("Step without delay after step with delay")
    # check ascending order of delays
    for step in policy[1:]:
        assert step.apply_after_seconds is not None
        prev_delay = prev.apply_after_seconds or 0  # if prev as instant
        if not step.apply_after_seconds > prev_delay:
            raise ValueError("Policy steps not ordered by delay")
        prev = step


def make_policy(policy: PolicySteps,
                ordering_key: Optional[str] = None) -> VanishingPolicy:
    """Creates or gets (when already existing) a VanishingPolicy
     with the given dict and return the created object

    Parameters
    ----------
    policy : List[Precision]
        List of precision reduction steps.
        The list must be sorted by ascending delay.

    ordering_key : string
        string containing the unique key for vanishing context.
         (Optional)

    Returns
    -------
    VanishingPolicy
        The created Policy
    """
    validate_policy(policy)
    vanpol, _created = VanishingPolicy.objects.get_or_create(
        policy=policy,
        ordering_key=ordering_key,
    )
    return vanpol
