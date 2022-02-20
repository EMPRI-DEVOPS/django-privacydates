django-privacydates
===================

**Disclaimer:** This project is an academic demonstrator and should be used with caution. We are happy to receive feedback but cannot guarantee any regular maintenance.

Django-privacydates is a Django app that provides alternatives to the common timestamp model fields
`DateField` and `DateTimeField`.
It is intended to provide developers with more data-minimal and
privacy-preserving model fields for common date-related purposes.

Privacydates is developed as part of the [EMPRI-DEVOPS research project](https://empri-devops.de)
which investigates and tackles privacy risks related to timestamping user
activity in application software.
The concepts and design are published in [an academic paper](https://svs.informatik.uni-hamburg.de/publications/2022/2022-01_Burkert_PrivacyDates.pdf) that will be
presented at the conference [GI SICHERHEIT 2022](https://www.sicherheit2022.kit.edu).
Citing recommendation are provided below.


## Basic Idea

Privacydates provides three basic types of alternatives to `DateTimeField` that
should be chosen depending on the individual use case:

1. `RoughDateField`: A `DateTimeField` compatible field that automatically _reduces the
   precision_ to a given level (e.g. 15 minute increments).
2. `VanishingDateField`: A more complex alternative that allows gradual
   precision reductions over time (e.g., 15 minute precision on creation and 1
   hour precision after 6 hours).
3. `OrderingDateField`: Not actually a date but a auto-incrementing
   sequence number that orders model instances within a given context.
   Dates are often use to achieve such ordering.
   By nature, a date has a global context which makes instances temporally
   comparable to any other event. Information that might not be need or wanted.
   `OrderingDateField` enforces you to pick a context to limit comparability.


### What is the right alternative for me?

Ask yourself the following questions:
_Did I need the `DateTimeField` for same app logic or just to provide user
with information?_ If the purpose is user information then you want to maintain
the comparability with dates and events outside of your app.
In that case, the choice is between `RoughDateField` and `VanishingDateField`.

You should choose `VanishingDateField` if you initially need higher date
precision for newly created instances but are fine with reducing the precision
over time. However, they introduce more overhead and require more code change.

`RoughDateField` is the correct choice if you never really need precise to the
second timestamps and are fine with reducing their precision from the
beginning. They are easy to adopt and behave like `DateTimeField`.

If your app employs timestamps for programmatic logic only, e.g.,
to keep track, which message a user has already seen and which are new,
you should consider using `OrderingDateField`.
As mentioned before, it is not really a date, so you cannot make any temporal
comparisons with outside events, but it is sufficient to keep the temporal order
of objects related to the same given context.
In the message example, the context could be a message room identifier and the state information kept for
each user could be the ordering number of the last seen post, instead of a timestamps when a user last viewed a room.


### Missing the right alternative for you?

The design of these alternatives are based on several case studies of applications.
If for some reason, you have use cases for timestamps that can not be met by our alternatives,
feel free to get in touch.
We like to learn more about developer demand and potentially extend our provided alternatives.


## Setup

1. Add `privacydates` to your INSTALLED_APPS setting like this::

```python
INSTALLED_APPS = [
    ...
    'privacydates',
]
```

2. Run ``python manage.py migrate`` to create the privacydates models.


## Usage

### Rough Date

The field named `RoughDateField` can be used as a direct replacement for `DateTimeField`.
It reduces the precision of the timestamp to a level given in multiples of time units like seconds or weeks,
as known from `timedelta` from the `datetime` package.
All parameters of `DateTimeField` can still be used.

In the following example, the created timestamp is reduced to a precision of 5 minutes increments.

```python
from django.db import models
from privacydates.fields import RoughDateField

class MyModel(models.Model):
    created = RoughDateField(minutes=5)
```


---
### Vanishing Date

`VanishingDateField` holds a foreign key reference to an auxiliary model called `VanishingDateTime`,
which stores the timestamp and additional information about the reduction policy that details how the timestamp precision
should be adjusted over time.

To use `VanishingDateField`, you first declare the field in your model definition.
Note that this is not compatible with `DateTimeField` so you can not use any of its specific parameters.

```python
from django.db import models
from privacydates.fields import VanishingDateField

class MyModel(models.Model):
    created = VanishingDateField()
```

The reduction policy used for vanishing date can be changed for each instance.
The following example shows how use create and assign a vanishing date to a `VanishingDateField`
using `VanishingFactory`.


```python
from django.utils import timezone
from privacydates.precision import Precision
from privacydates.vanish import VanishingFactory
from .models import MyModel

def some_request_handler(request):
    # ...
    factory = VanishingFactory(policy=[
        Precision(minutes=1),
        Precision(minutes=15).after(minutes=5),
        Precision(hours=1).after(minutes=30),
    ])

    my_instance = MyModel(
        created=factory.create(timezone.now()),
    )
    # ... you can access the date like this
    thedate = my_instance.created.dt
```

`VanishingFactory` is set up in this example to create dates which have their precision reduced in three stages.
The first immediately on creation (no after) to a precision of 1 minute.
The second after 5 minutes to 15 minutes, and the third after 30 minutes to a level of 1 hour.

Note that to **execute the reduction policy** you either have to set up a cron job that regularly triggers the processing of due reductions,
or you call the respective trigger manually. See below for more detailed setup instructions.

---
### Ordering Date

`OrderingDateField` is intended for timestamps that are used solely for preserving temporal order within a logical context.
It holds an integer representing its position in a temporal sequence defined by a context.
Hence, sequences are separated from each other by the use of contexts. Each context has a unique key.
In it the counter increments on each new assignment, starting at 1.
Behind the scenes, `OrderingDateField` is an `IntegerField`.

To use ordering date, you add the field to you model definition.
Note that the
As shown in the following example, you can also specify that ordering keys
should be hashed before storing in the database

```python
from django.db import models
from privacydates.fields import OrderingDateField

class MyModel(models.Model):
    created = OrderingDateField(hashed=True)
```


During model instantiation the context key is assigned to field.
If this context key has not been used before, a new context will be created and stored.
Otherwise, the key will be used to determine the next ordering number of the existing context.
If `hashed` has been set to `True` in the field declaration, context key values will be hashed
with SHA256 before storing.

```python
from .models import MyModel

def some_request_handler(request):
    # ...
    my_instance = MyModel(
        created="my-context-key",
    )
    # ...
```

Note that `OrderingDateField` does not hold any information about the context used to determine its
ordering number. If you need this information, make sure it can be derived from other model information.


## Setup execution of vanishing policy

The enforcement of reduction policies for vanishing dates relies on periodic external triggers.
This can be done by calling a management command, e.g., via a cron job, or by calling the vanishing updater directly.

The interval between the invocations of the trigger should correspond to the minimum `after` delay specified in any policy.
For instance, to enforce the policy step `Precision(minutes=5).after(minutes=1)`, the trigger should be invoked at least every minute.
The larger the interval, the lower the accuracy with which the specified `after` delay can be adhered to.
Choose a trigger interval that is acceptable as an enforcement delay for your `after` values.


### Invoke management command via cron job

We provide the management command `vanishdates` that can be executed from your projects `manage.py`:

```
$ ./manage.py vanishdates
```

In order to periodically call this management command, you can use Cron.
Cron allows to schedule tasks as frequently as every minute.
If your scenario requires a sub-minutes frequency, consider using systemd timers.
The following example triggers the management command every minute.
Add it to `/etc/crontab`:

```
# periodically triggers date vanishing
*/1 * * * * <username> cd <project-dir> && ./manage.py vanishdates
```

Adjust `<username>`  and `<project-dir>` to your Django setup.


### Invoke hook from Django

If you want to invoke the vanishing process from your Django code, you can do it like this:

```python
from privacydates.vanish import update_vanishing

def some_function():
    # ...
    update_vanishing()
    # ...
```


## Citation information

If you use `django-privacydates` in relation with academic projects and publications,
we would be happy to receive citations of the following related paper:

```
@inproceedings{burkertPrivacyDatesFramework2022,
  title = {{{PrivacyDates}}: {{A Framework}} for {{More Privacy-Preserving Timestamp Data Types}}},
  author = {Burkert, Christian and Balack, Jonathan and Federrath, Hannes},
  date = {2022},
  series = {Lecture {{Notes}} in {{Informatics}} ({{LNI}})},
  location = {{Karlsruhe}},
  eventtitle = {{{GI Sicherheit}} 2022},
}
```
