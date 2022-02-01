django-privacydates
===================

**Disclaimer:** This project is an academic demonstrator and be used with caution. We are happy to receive feedback but cannot guarantee any regular maintenance.

Privacydates is a Django app that provides alternatives to the common timestamp model fields
`DateField` and `DateTimeField`.
It is intended to provide developers with more data minimal and
privacy-preserving model fields for common date-related purposes.

Privacydates is developed as part of the [EMPRI-DEVOPS research project](https://empri-devops.de)
which investigates and tackles privacy risks related to timestamping user
activity in application software.


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

The field named `RoughDateField` can be used as one to one replacement for a DateTimeField.
It reduces the precision of the timestamp by a given value.

Import it with:

```python
from privacydates.fields import RoughDateField
```

Replace the `DateTimeField` with it. All parameters can still be used.
Add the parameter `reduction_value` with the targeted precision in seconds as integer.

Example:
```python
timestamp = RoughDateField(reduction_value=60)
```
to reduce the accuracy to one minute.


---
### Vanishing Date

The field named `VanishingDateField` only saves a ForeignKey to a `VanishingDateTime`.
The timestamp is placed in VanishingDateTime.

Import it with:

```python
from privacydates.fields import VanishingDateField
```


Replace the DateTimeField with the VanishingDateField. Only Parameters applicable for RelationFields can be used.
Example of the definition:
```python
timestamp = VanishingDateField()
```

The goal of vanishing is to provide a timestamp that loses accuracy over time.
For this, a set of rules must be created according to which these accuracy reductions are made.
An `AnnihilationPolicy` is created with the set of rules.

To create one import:

```python
from privacydates.vanish import make_policy
```

and create a dictionary in this scheme:

```python
policy_dict = {
        "events": [
            {
                "offset": 60,
                "reduction": 120
            },
            {
                "offset": 120,
                "reduction": 86400
            },
        ],
    }
```
- offset sets the time period after which an vanishing event should take place. (in minutes)
- reduction is the target precision for the vanishing event. (in seconds)

Create a VanishingPolicy with:
```python
make_policy(policy_dict)
```


To initialize a timestamp,
a VanishingDateTime object must be created and this must be passed to the VanishingDateField.
To create a VanishingDateTime use the method `vanishingdatetime_creator`.

Import it with:

```python
from privacydates.vanish import vanishingdatetime_creator
```

Example of usage:
```python
timestamp = vanishingdatetime_creator(
    timezone.now(),
    vanishing_policy_creator(policy_dict)
)
```

To print the timestamp in VanishingDateTime:
```python
print(timestamp.dt)
```



---
### Ordering Date

The field named `OrderingDateField` is intended for timestamps that are used solely for sorting objects.
It only saves an Integer for every timestamp in the database representing its position in a sequence.
Sequences are separated from each other by the use of contexts. Each context has a unique key.
In it the counter increments at each allocation, starting at 1.
To create an ordering key make use of the method `ordering_key_gen`

Import it with:

```python
from privacydates.fields import OrderingDateField
from privacydates.order import ordering_key_gen
```


Replace the DateTimeField with the OrderingDateField. Only Parameters applicable for IntegerFields can be used.
Example of the Definition:
```python
timestamp = OrderingDateField()
```


At initialization the context key is passed.
Example of initialization:
```python
timestamp = ordering_key_gen("this-is-an-ordering-key")
```

Whenever you want to get the value just do it as if it were an IntergerField.
