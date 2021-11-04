import uuid

from django.db import models
from django.utils import timezone

from .rough import roughen_datetime


class VanishingPolicy(models.Model):
    """Model used by VanishingDateTime for storing the rules that
     specify the VanishingEvents
    """
    policy = models.JSONField()
    ordering_key = models.CharField(null=True, blank=True, max_length=64)

    class Meta:
        unique_together = ('policy', 'ordering_key',)


class VanishingDateTime(models.Model):
    """Model that implements Time Unit Annihilation for
     Django DateTimeFields.

    Parameters
    ----------
    dt : datetime.datetime
        initial and internal datetime.datetime,
         of which information vanishes
        The datetime which should be reduced

    vanishing_policy: VanishingPolicy
        Instance of VanishingPolicy defining the vanishing plan
         and controlling ordering functionality
    """
    dta_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt = models.DateTimeField()
    vanishing_policy = models.ForeignKey(VanishingPolicy, on_delete=models.DO_NOTHING)

    class Meta:
        ordering = ('dt', )

    def __str__(self):
        return str(self.dt)


class VanishingEvent(models.Model):
    """An VanishingEvent represent a single plannend Vanishing
     of one VanishingDateTime instance on a given point of time.
    Instances are regulary created by event_creator

    Parameters
    ----------
    vanishing_datetime : VanishingDateTime
        The VanishingDateTime instance the event is set for

    event_date: datetime.datetime
        The date and time the vanishing event is scheduled at.

    iteration: integer
        the iteration of vanishing events for vanishing_datetime
    """
    vanishing_datetime = models.ForeignKey(VanishingDateTime, on_delete=models.CASCADE)
    event_date = models.DateTimeField()
    iteration = models.IntegerField()


class OrderingContext(models.Model):
    """Model managing Ordering

    Parameters
    ----------
    context_key : String
        Django CharField (max_length=64) as unique identifier for
         the instance

    last_count: integer
        Last count given by the instance

    last_date: datetime.datetime
        The roughend Date the last count was given

    similarity_distance: integer
        the length of the roughend time slot in seconds
    """
    context_key = models.CharField(primary_key=True, max_length=64, editable=False)
    last_count = models.IntegerField(default=0)
    similarity_distance = models.IntegerField(default=0)
    last_date = models.DateTimeField(null=True)

    def get_and_increment(self) -> int:
        """Get the next count (lowest unused) from an instance of
        OrderingContext. If similarity_distance is set to be > 0

        the same count is given for timestamps in the same generalized
        time slot. The size is defined by similarity_distance

        Returns
        -------
        int
            lowest unused number of the context
        """
        if self.similarity_distance >= 1:
            rough_now = roughen_datetime(timezone.now(),
                                               self.similarity_distance)

            if self.last_date is not None and self.last_date == rough_now:
                return self.last_count
            self.last_date = rough_now

        self.last_count += 1
        self.save()
        return self.last_count


class VanishingOrderingContext(models.Model):
    """Model managing the count in Ordering of Vanishing.
    For Vanishing the counter resets,
    when the VanishingDateTime is or will be different.

    Parameters
    ----------
    context_key : String
        Django CharField (max_length=64) as unique identifier for the instance

    last_count: integer
        Last count given by the instance

    last_date: datetime.datetime
        Last time the context was used
    """
    context_key = models.CharField(primary_key=True, max_length=64, editable=False)
    last_count = models.IntegerField(default=0)
    last_date = models.DateTimeField(null=True, blank=True)


    def get_and_increment(self, policy: VanishingPolicy) -> int:
        """Get the next count from an instance of OrderingContext.

        Parameters
        ----------
        policy : VanishingPolicy
            VanishingPolicy used for the
             of VanishingDateTime

        Returns
        -------
        int
            lowest unused number of the context, since the last reset
        """
        max_reduction = max([e['reduction'] for e in policy.policy['events']])
        roughed_now = roughen_datetime(timezone.now(), max_reduction)
        if self.last_date is None or self.last_date != roughed_now:
            self.last_count = 0
            self.last_date = roughed_now
            self.save()
            return self.last_count
        if self.last_count >= 999999:
            return self.last_count
        self.last_count = self.last_count + 1
        self.save()
        return self.last_count
