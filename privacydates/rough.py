"""
Datetime precision reduction utilites
"""
from datetime import datetime, timezone


def roughen_datetime(dt: datetime, reduction_value: int) -> datetime:
    """Reduces the datetimes precision to multiples of the given value in
    seconds.

    Note that the reduction is done on the local not UTC timestamp.
    As a result, the UTC value of a CET timestamp after reduction to
    day-precision will still show an hour-value of 1 due to the timezone
    offset.

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
        The rough datetime


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

    # pretend timestamp is UTC avoid offset ajustment when calculating
    # POSIX timestamp. Otherwise we would reduce the UTC value.
    reduced_unixtime = ((int(dt.replace(tzinfo=timezone.utc).timestamp())
                         // reduction_value) * reduction_value)

    # carry over tzinfo if existant
    return datetime.utcfromtimestamp(
        reduced_unixtime).replace(tzinfo=dt.tzinfo)
