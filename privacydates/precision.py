"""Date precision utilities"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional


class Precision:
    """Precision class for specifying the precision level of dates."""
    def __init__(self, seconds=0, minutes=0, hours=0, days=0, weeks=0,
                 months=0, years=0, after_seconds=0) -> None:
        """
        Precisions can be given calendar-dependent as multiples of months and
        years, or as multiples of calendar-independ time units like days or
        hours.

        Calendar dependent and independent precision values can not be combined.
        """
        # first check calendar independent units
        delta = timedelta(days=days, seconds=seconds, minutes=minutes,
                          hours=hours, weeks=weeks)
        total_sec = int(delta.total_seconds())

        if not (total_sec or months or years):
            raise ValueError("You must specify a reduction value "
                             "other than zero")
        if total_sec and (months or years):
            raise ValueError("You can not combine calender dependent and "
                             "independent precisions")
        if months and years:
            raise ValueError("You can not combine month and year precision")

        if months < 0 or months > 12:
            raise ValueError("months must be between 0 and 12")
        if months and 12 % months != 0:
            raise ValueError("months must be divisor of 12")

        if years < 0:
            raise ValueError("years must be positive")
        if total_sec < 0:
            raise ValueError("reduction values must be positive")

        self.seconds = total_sec
        self.months = months
        self.years = years
        self.apply_after_seconds: Optional[int] = after_seconds or None

    def apply(self, dt: datetime) -> datetime:
        """Apply the precision level to the given date and return the reduced
        date."""
        if self.seconds:
            return reduce_precision(dt, self.seconds)
        dt = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if self.months:
            return dt.replace(month=(dt.month // self.months)*self.months)
        if self.years:
            dt = dt.replace(month=1)
            return dt.replace(year=(dt.year // self.years)*self.years)
        raise RuntimeError("Unexpected precision")

    def after(self, seconds=0, minutes=0, hours=0, days=0, weeks=0) -> 'Precision':
        """Set a delay after which the precision should be applied.
        This is for usage in combination with VanishingDate.
        Return the modified Precision for chaining.
        """
        delay = timedelta(days=days, seconds=seconds, minutes=minutes,
                          hours=hours, weeks=weeks)
        total_sec = int(delay.total_seconds())
        if total_sec < 0:
            raise ValueError("A possitive delay must be given")
        self.apply_after_seconds = total_sec
        return self

    @property
    def apply_after_timedelta(self) -> timedelta:
        if self.apply_after_seconds is None:
            raise ValueError("No apply delay set")
        return timedelta(seconds=self.apply_after_seconds)

    def is_applied_immediately(self) -> bool:
        """Return if precision should apply immediately or not."""
        return (self.apply_after_seconds is None
                or self.apply_after_seconds == 0)

    def __repr__(self) -> str:
        fmt = "Precision(%s=%d)"
        if self.seconds:
            return fmt % ("seconds", self.seconds)
        if self.months:
            return fmt % ("months", self.months)
        if self.years:
            return fmt % ("years", self.years)
        raise RuntimeError("Unexpected precision")

    def to_dict(self) -> Dict[str, int]:
        return dict(
            seconds=self.seconds,
            months=self.months,
            years=self.years,
            after_seconds=self.apply_after_seconds or 0,
        )

    @classmethod
    def from_dict(cls, precision_dict: Dict[str, int]) -> "Precision":
        return cls(
            seconds=precision_dict["seconds"],
            months=precision_dict["months"],
            years=precision_dict["years"],
            after_seconds=precision_dict["after_seconds"],
        )


def reduce_precision(dt: datetime, reduction_divisor: int) -> datetime:
    """Reduces the datetimes precision to multiples of the given reduction
    divisor in seconds.

    Note that the reduction is done on the local not UTC timestamp.
    As a result, the UTC value of a CET timestamp after reduction to
    day-precision will still show an hour-value of 1 due to the timezone
    offset.

    Parameters
    ----------
    dt : datetime.datetime
        The datetime which should be reduced
    reduction_divisor : int
        The value that indicates the precision level in seconds
         (e.g. 60 would achieve an accuracy of one minute)

    Returns
    -------
    datetime.datetime
        The reduced datetime
    """
    if not isinstance(dt, datetime):
        raise TypeError("dt must be datetime (was %s)" % type(dt))
    if not isinstance(reduction_divisor, int):
        raise TypeError("reduction_divisor must be int (was %s)"
                        % type(reduction_divisor))
    if reduction_divisor <= 0:
        raise ValueError("reduction_divisor must be positive")
    # pretend timestamp is UTC avoid offset ajustment when calculating
    # POSIX timestamp. Otherwise we would reduce the UTC value.
    reduced_unixtime = (
        (int(dt.replace(tzinfo=timezone.utc).timestamp())
         // reduction_divisor) * reduction_divisor
    )

    # carry over tzinfo if existant
    return datetime.utcfromtimestamp(reduced_unixtime).replace(tzinfo=dt.tzinfo)
