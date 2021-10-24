from datetime import datetime
from django import template
from django.utils.timezone import make_aware

register = template.Library()

@register.filter
def enum_to_date(value: int) -> datetime:
    """Custom Django Template Filter transforming the EnumerationDateTime
     output (int) into a datetime object.

        Parameters
        ----------
        value : int
            Filter input is a integer

        Returns
        -------
        datetime.datetime
            The generalized Datetime
        """
    if value is None:
        return value
    try:
        return make_aware(datetime.fromtimestamp(int(value)))
    except TypeError:
        raise TypeError("Filter enum_to_date expects an integer as input, but got "
                        + str(type(value)))
