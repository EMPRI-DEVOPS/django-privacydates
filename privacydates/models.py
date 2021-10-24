import uuid

from django.db import models
from django.utils import timezone

from .generalization import generalize_datetime


class AnnihilationPolicy(models.Model):
    """Model used by DateTimeAnnihilation for storing the rules that
     specify the AnnihilationEvents
    """
    policy = models.JSONField()
    enumeration_key = models.CharField(null=True, blank=True, max_length=64)

    class Meta:
        unique_together = ('policy', 'enumeration_key',)


class DateTimeAnnihilation(models.Model):
    """Model that implements Time Unit Annihilation for
     Django DateTimeFields.

    Parameters
    ----------
    dt : datetime.datetime
        initial and internal datetime.datetime,
         which is being annihilated
        The datetime which should be reduced

    annihilationpolicy: AnnihilationPolicy
        Instance of AnnihilationPolicy defining the annihilation plan
         and controlling enumeration functionality
    """
    dta_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dt = models.DateTimeField()
    annihilation_policy = models.ForeignKey(AnnihilationPolicy, on_delete=models.DO_NOTHING)

    class Meta:
        ordering = ('dt', )

    def __str__(self):
        return str(self.dt)


class AnnihilationEvent(models.Model):
    """An AnnihilationEvent represent a single plannend Annihilation
     of one DateTimeAnnihilation instance on a given point of time.
    Instances are regulary created by event_creator

    Parameters
    ----------
    datetime_annihilation : DateTimeAnnihilation
        The DateTimeAnnihilation instance the event is set for

    event_date: datetime.datetime
        The date and time the annihilation event is scheduled at.

    iteration: integer
        the iteration of annihilation events for datetimeannihilation
    """
    datetime_annihilation = models.ForeignKey(DateTimeAnnihilation, on_delete=models.CASCADE)
    event_date = models.DateTimeField()
    iteration = models.IntegerField()


class EnumerationContext(models.Model):
    """Model managing Enumeration

    Parameters
    ----------
    context_key : String
        Django CharField (max_length=64) as unique identifier for
         the instance

    last_count: integer
        Last count given by the instance

    last_date: datetime.datetime
        The generalized Date the last count was given

    similarity_distance: integer
        the length of the generalizition time slot in seconds
    """
    context_key = models.CharField(primary_key=True, max_length=64, editable=False)
    last_count = models.IntegerField(default=0)
    similarity_distance = models.IntegerField(default=0)
    last_date = models.DateTimeField(null=True)


    def get_and_increment(self) -> int:
        """Get the next count (lowest unused) from an instance of
        EnumerationContext. If similariry_distance is set to be > 0

        the same count is given for timestamps in the same generalized
        time slot. The size is defined by similarity_distance

        Returns
        -------
        int
            lowest unused number of the context
        """
        if self.similarity_distance >= 1:
            generalized_now = generalize_datetime(timezone.now(),
                                                  self.similarity_distance)

            if self.last_date is not None and self.last_date == generalized_now:
                return self.last_count
            self.last_date = generalized_now

        self.last_count += 1
        self.save()
        return self.last_count


class AnnihilationEnumContext(models.Model):
    """Model managing the count in Enumeration of Annihilation.
    For Annihilation the counter resets,
    when the AnnihilationDateTime is or will be different.

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


    def get_and_increment(self, policy: AnnihilationPolicy) -> int:
        """Get the next count from an instance of EnumerationContext.

        Parameters
        ----------
        policy : AnnihilationPolicy
            AnnihilationPolicy used for the
             of DateTimeAnnihilation

        Returns
        -------
        int
            lowest unused number of the context, since the last reset
        """
        max_reduction = max([e['reduction'] for e in policy.policy['events']])
        generalized_now = generalize_datetime(timezone.now(), max_reduction)
        if self.last_date is None or self.last_date != generalized_now:
            self.last_count = 0
            self.last_date = generalized_now
            self.save()
            return self.last_count
        if self.last_count >= 999999:
            return self.last_count
        self.last_count = self.last_count + 1
        self.save()
        return self.last_count
