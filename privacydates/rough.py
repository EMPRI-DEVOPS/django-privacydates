import math
from datetime import datetime
from django.utils.timezone import is_aware


def roughen_datetime(dt: datetime, reduction_value: int) -> datetime:
    """Roughens Datetimes by a passed value

    Parameters
    ----------
    dt : datetime.datetime
        The datetime which should be reduced
    reduction_value : int
        The value that indicates the roughing factor in seconds
         (e.g. 60 would achieve an accuracy of one minute)

    Returns
    -------
    datetime.datetime
        The rough Datetime


    Raises
    -------
    TypeError
        If dt is not of type datetime
    TypeError
        If reduction_value is not of type int
    ValueError
        If reduction_value is not smaller than 1.

    """
    if not isinstance(dt, datetime):
        raise TypeError('invalid type of dt')
    if not isinstance(reduction_value, int):
        raise TypeError('invalid type of reductionvalue')
    if reduction_value < 1:
        raise ValueError('invalid value passed for reductionvalue')

    # Generalization formular. Datetime is converted to timestamp (unixtime)
    reduced_unixtime = (math.floor(int(dt.timestamp())
                                   / reduction_value)
                        * reduction_value)

    # If the input datetime was timezone aware, this will be reflected by the new datetime
    if is_aware(dt):
        reduced_dt = datetime.fromtimestamp(reduced_unixtime, tz=dt.tzinfo)
    else:
        reduced_dt = datetime.fromtimestamp(reduced_unixtime)
    return reduced_dt
