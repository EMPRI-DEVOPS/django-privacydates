"""Auxiliary models for maintaining vanishing dates"""
import uuid
import warnings

from django.db import models
from django.utils import timezone

from .precision import Precision, reduce_precision
from .policy import PolicyEncoder, PolicyDecoder


class VanishingPolicy(models.Model):
    """Model used by VanishingDateTime for storing the rules that
     specify the VanishingEvents
    """
    policy = models.JSONField(encoder=PolicyEncoder, decoder=PolicyDecoder)
    ordering_key = models.CharField(null=True, blank=True, max_length=64)

    class Meta:
        unique_together = ('policy', 'ordering_key',)


class VanishingDateTime(models.Model):
    """Stores datetime and policy information for a vanishing date

    Parameters
    ----------
    dt : datetime
        Initial datetime of which information vanishes

    vanishing_policy: VanishingPolicy
        Instance of VanishingPolicy defining the reduction policy
        and controlling the optional ordering context.
    """
    dta_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt = models.DateTimeField()
    vanishing_policy = models.ForeignKey(VanishingPolicy, on_delete=models.DO_NOTHING)

    class Meta:
        ordering = ('dt', )

    def __str__(self):
        return str(self.dt)


class VanishingEvent(models.Model):
    """A VanishingEvent represent a single plannend reduction step
     of one VanishingDateTime instance on a given point of time.

    Parameters
    ----------
    vanishing_datetime : VanishingDateTime
        The VanishingDateTime instance the event is set for

    event_date: datetime
        The date and time the vanishing event is scheduled at

    iteration: int
        The step number within the vanishing policy
    """
    vanishing_datetime = models.ForeignKey(VanishingDateTime,
                                           related_name="events",
                                           on_delete=models.CASCADE)
    event_date = models.DateTimeField()
    iteration = models.IntegerField()


class OrderingContext(models.Model):
    """Model managing Ordering

    Parameters
    ----------
    context_key : str
        64 character key unique identifier for the context

    last_count: int
        Last count or ordering number assigned for this context

    last_date: datetime
        Datetime when the last count was assigned

    similarity_distance: int
        Length in seconds of time slot within items share the same ordering
        number
    """
    context_key = models.CharField(primary_key=True, max_length=64, editable=False)
    last_count = models.IntegerField(default=0)
    similarity_distance = models.IntegerField(default=0)
    last_date = models.DateTimeField(null=True)

    def next(self) -> int:
        """Get the next count (lowest unused).
        If similarity_distance is >0, the same count is given for timestamps in
        the same rouged time slot.

        Returns
        -------
        int
            lowest unused number of the context
        """
        if self.similarity_distance > 0:
            rough_now = reduce_precision(timezone.now(),
                                         self.similarity_distance)
            if self.last_date and self.last_date == rough_now:
                # within similarity distance
                return self.last_count
            self.last_date = rough_now
        self.last_count += 1
        self.save()
        return self.last_count


class VanishingOrderingContext(models.Model):
    """Stores the ordering count for vanishing dates.

    The counter resets, when the next VanishingDateTime is or will be
    different form the last at maximum reduction level.

    Parameters
    ----------
    context_key : str
        64 character key unique identifier for the context

    last_count: int
        Last count or ordering number assigned for this context

    last_date: datetime
        Datetime when the last count was assigned
    """
    context_key = models.CharField(primary_key=True, max_length=64,
                                   editable=False)
    last_count = models.IntegerField(default=0)
    last_date = models.DateTimeField(null=True, blank=True)

    def next(self, policy: VanishingPolicy) -> int:
        """Get the next count.

        Parameters
        ----------
        policy : VanishingPolicy
            VanishingPolicy used to determine the maximum reduction level.

        Returns
        -------
        int
            lowest unused number of the context, since the last reset
        """
        last_precision: Precision = policy.policy[-1]  # last reduction step
        roughed_now = last_precision.apply(timezone.now())
        if self.last_count >= 999999:
            warnings.warn("Overflow in ordering counter %s" % self.context_key)
            return self.last_count
        if not self.last_date or self.last_date != roughed_now:
            self.last_count = 0
            self.last_date = roughed_now
        else:
            self.last_count += 1
        self.save()
        return self.last_count
