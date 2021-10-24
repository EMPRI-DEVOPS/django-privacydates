"""
Django model data fields for storing datetimes
in a more privacy preserving format
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .generalization import generalize_datetime
from .models import EnumerationContext, DateTimeAnnihilation


class GeneralizationField(models.DateTimeField):
    """Django field storing a generalized datetime.datetime
    """
    description = _("Generalized Date (with time)")

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
        return generalize_datetime(dt, self.reduction_value)


class EnumerationField(models.IntegerField):
    """Django Field implementing a counter for sequence
    or revision numbers
    """
    description = _("Enumeration for sequence or revision counter")

    def __init__(self, similarity_distance=0, *args, **kwargs):
        self.similarity_distance = similarity_distance
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['similarity_distance'] = self.similarity_distance
        return name, path, args, kwargs


    def pre_save(self, model_instance, add):
        # Get EnumerationContext for given context_key
        field_input = getattr(model_instance, self.attname)
        if field_input is None:
            return field_input
        if type(field_input) is int:
            return field_input
        if type(field_input) is not str:
            raise TypeError('Enumeration key must be a string, but is ' + str(type(field_input)))
        context_object, created = EnumerationContext.objects.\
            get_or_create(context_key=field_input,
                          similarity_distance=self.similarity_distance)
        # Get count from EnumerationContext
        count = context_object.get_and_increment()
        return count


class AnnihilationField(models.OneToOneField):
    """Django Field so save an one-to-to relation to an instance of
     DateTimeAnnihilation
    """
    description = _("Field handles relationship to DateTimeAnnihilation")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('on_delete', models.CASCADE)
        kwargs.setdefault('to', DateTimeAnnihilation)
        kwargs.setdefault('related_name', '+')
        super().__init__( *args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs
