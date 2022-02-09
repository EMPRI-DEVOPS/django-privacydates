"""
Django model data fields for storing datetimes
in a more privacy preserving format
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .models import OrderingContext, VanishingDateTime
from .order import hash_context_key
from .precision import Precision


class RoughDateField(models.DateTimeField):
    """Django field storing a rough datetime.datetime
    """
    description = _("Rough Date (with time)")

    def __init__(self, *args, seconds=0, minutes=0, hours=0, days=0, weeks=0,
                 months=0, years=0, **kwargs) -> None:
        """DateTimeField with reduced precision.
        Precisions can be given calendar-dependent as multiples of months and
        years, or as multiples of calendar-independ time units like days or
        hours.

        Calendar dependent and independent precision values can not be combined.
        """
        self.precision = Precision(seconds, minutes, hours, days, weeks,
                                   months, years)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['seconds'] = self.precision.seconds
        kwargs['months'] = self.precision.months
        kwargs['years'] = self.precision.years
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        dt = super().pre_save(model_instance, add)
        if dt is None:
            return dt
        rough_dt = self.precision.apply(dt)
        setattr(model_instance, self.attname, rough_dt)
        return rough_dt


class OrderingDateField(models.IntegerField):
    """Django Field implementing a counter for sequence
    or revision numbers
    """
    description = _("Ordering Date for sequence or revision counter")

    def __init__(self, *args, similarity_distance=0, hashed=False, **kwargs):
        self.similarity_distance = similarity_distance
        self.hashed = hashed
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['similarity_distance'] = self.similarity_distance
        kwargs['hashed'] = self.hashed
        return name, path, args, kwargs


    def pre_save(self, model_instance, add):
        """If the value assigned to the field is a str then treat it as a
        context key, fetch the next ordering number and use it as field value
        instead.
        """
        field_input = getattr(model_instance, self.attname)
        if field_input is None:
            return field_input
        if isinstance(field_input, int):
            return field_input
        if not isinstance(field_input, str):
            raise TypeError('Ordering key must be a string, but is '
                            + str(type(field_input)))
        key = field_input
        if self.hashed:
            key = hash_context_key(key)
        context, _ = OrderingContext.objects.get_or_create(
            context_key=key,
            similarity_distance=self.similarity_distance,
        )
        return context.next()


class VanishingDateField(models.OneToOneField):
    """Django Field so save an one-to-to relation to an instance of
     VanishingDateTime
    """
    description = _("Field handles relationship to VanishingDateTime")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('on_delete', models.CASCADE)
        kwargs.setdefault('to', VanishingDateTime)
        kwargs.setdefault('related_name', '+')
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs
