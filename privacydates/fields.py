"""
Django model data fields for storing datetimes
in a more privacy preserving format
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .models import OrderingContext, VanishingDateTime
from .precision import reduce_precision


class RoughDateField(models.DateTimeField):
    """Django field storing a rough datetime.datetime
    """
    description = _("Rough Date (with time)")

    def __init__(self, reduction_value=1, *args, **kwargs):
        self.reduction_value = reduction_value
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['reduction_value'] = self.reduction_value
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        dt = super().pre_save(model_instance, add)
        if dt is None:
            return dt
        rough_dt = reduce_precision(dt, self.reduction_value)
        setattr(model_instance, self.attname, rough_dt)
        return rough_dt


class OrderingDateField(models.IntegerField):
    """Django Field implementing a counter for sequence
    or revision numbers
    """
    description = _("Ordering Date for sequence or revision counter")

    def __init__(self, similarity_distance=0, *args, **kwargs):
        self.similarity_distance = similarity_distance
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['similarity_distance'] = self.similarity_distance
        return name, path, args, kwargs


    def pre_save(self, model_instance, add):
        # Get OrderingContext for given context_key
        field_input = getattr(model_instance, self.attname)
        if field_input is None:
            return field_input
        if type(field_input) is int:
            return field_input
        if type(field_input) is not str:
            raise TypeError('Ordering key must be a string, but is ' + str(type(field_input)))
        context_object, created = OrderingContext.objects.\
            get_or_create(context_key=field_input,
                          similarity_distance=self.similarity_distance)
        # Get count from OrderingContext
        count = context_object.get_and_increment()
        return count


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
