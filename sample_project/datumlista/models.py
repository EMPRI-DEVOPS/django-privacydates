from django.db import models
from django.utils import timezone

from privacydates import fields
from privacydates.mixins import VanishingDateMixIn


# Basic Event with multiple timestamps representing the same time with the different types of privacydates date fields.
class Event(models.Model, VanishingDateMixIn):
    base_date = models.DateTimeField(null=True, blank=True, default=timezone.now)
    rough_date = fields.RoughDateField(default=timezone.now, null=True, blank=True, reduction_value=30)
    vanishing_date = fields.VanishingDateField()
    vanishing_ordering_date = fields.VanishingDateField()
    ordering_date = fields.OrderingDateField(null=True, blank=True)
    ordering_similarity_date = fields.OrderingDateField(null=True, blank=True, similarity_distance=2)