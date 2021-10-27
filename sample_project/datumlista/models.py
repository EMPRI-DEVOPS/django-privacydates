from django.db import models
from django.utils import timezone

from privacydates import fields
from privacydates.mixins import AnnihilationMixIn


# Basic Event with multiple timestamps representing the same time with different model fields.
class Event(models.Model, AnnihilationMixIn):
    base_date = models.DateTimeField(null=True, blank=True, default=timezone.now)
    generalized_date = fields.GeneralizationField(default=timezone.now, null=True, blank=True, reduction_value=30)
    annihilation_date = fields.AnnihilationField()
    annihilation_enumeration_date = fields.AnnihilationField()
    enumeration_date = fields.EnumerationField(null=True, blank=True)
    enumeration_similarity_date = fields.EnumerationField(null=True, blank=True, similarity_distance=2)