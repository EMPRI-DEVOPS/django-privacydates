from django.db import models
from django.utils import timezone

from privacydates import fields
from privacydates.mixins import VanishingDateMixIn


class Event(models.Model, VanishingDateMixIn):
    """Basic Event with multiple timestamps representing the same time with the
    different types of privacydates date fields."""
    base_date = models.DateTimeField(
        null=True, blank=True, default=timezone.now)
    rough_date = fields.RoughDateField(
        seconds=30,
        default=timezone.now, null=True, blank=True,
    )
    vanishing_date = fields.VanishingDateField()
    vanishing_ordering_date = fields.VanishingDateField()
    ordering_date = fields.OrderingDateField(null=True, blank=True, hashed=True)
    ordering_similarity_date = fields.OrderingDateField(
        null=True, blank=True, hashed=False, similarity_distance=2)

class VDEvent(models.Model, VanishingDateMixIn):
    date = fields.VanishingDateField()
