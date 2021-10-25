django-privacydates
===================

Privacydates is a Django app that provides alternatives to the common timestamp model fields
`DateField` and `DateTimeField`.
It is intended to provide developers with more data minimal and
privacy-preserving model fields for common date-related purposes.

Privacydates is developed as part of the [EMPRI-DEVOPS research project](https://empri-devops.de)
which investigates and tackles privacy risks related to timestamping user
activity in application software.


## Setup

1. Add `privacydates` to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'privacydates',
    ]

2. Run ``python manage.py migrate`` to create the privacydates models.


## Usage

### Generalization

The field named `GeneralizationField` can be used as one to one replacement for a DateTimeField.
It reduces the precision of the timestamp by a given value.

Import it with:
```python
from privacydates.fields import GeneralizationField
```

Replace the `DateTimeField` with it. All parameters can still be used.
Add the parameter `reduction_value` with the targeted precision in seconds as integer.

Example:
```python
timestamp = GeneralizationField(reduction_value=60)
```
to generalize it to one minute.


---
### Time Unit Annihilation

The field named `AnnihilationField` only saves a ForeignKey to a `DateTimeAnnihilation`.
The timestamp is placed in DateTimeAnnihilation.

Import it with:
```python
from privacydates.fields import AnnihilationField
```


Replace the DateTimeField with the AnnihilationField. Only Parameters applicable for RelationFields can be used.
Example of the definition:
```python
timestamp = AnnihilationField()
```

The goal of annihilation is to provide a timestamp that loses accuracy over time.
For this, a set of rules must be created according to which these accuracy reductions are made.
An `AnnihilationPolicy` is created with the set of rules.

To create one import:
```python
from privacydates.annihilation import annihilation_policy_creator
```

and create a dictionary in this scheme:

```json
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
- offset sets the time period after which an annihilation event should take place. (in minutes)
- reduction is the target precision for the annihilation event. (in seconds)

Create a AnnihilationPolicy with:
```python
annihilation_policy_creator(policy_dict)
```


To initialize a timestamp,
a DateTimeAnnihilation object must be created and this must be passed to the AnnihilationField.
To create a DateTimeAnnihilation use the method `datetimeannihilation_creator`.

Import it with:
```python
from privacydates.annihilation import datetimeannihilation_creator
```

Example of usage:
```python
timestamp = datetimeannihilation_creator(timezone.now(),annihilation_policy_creator(policy_dict)),
```

To print the timestamp in DateTimeAnnihilation:
```python
print(timestamp.dt)
```



---
### Enumeration

The field named `EnumerationField` is intended for timestamps that are used solely for sorting objects.
It only saves an Integer for every timestamp in the database representing its position in a sequence.
Sequences are separated from each other by the use of contexts. Each context has a unique key.
In it the counter increments at each allocation, starting at 1.
To create an enumeration key make use of the method `enumeration_key_gen`

Import it with:
```python
from privacydates.fields import EnumerationField
from privacydates.enumeration import enumeration_key_gen
```


Replace the DateTimeField with the EnumerationField. Only Parameters applicable for IntegerFields can be used.
Example of the Definition:
```python
timestamp = EnumerationField()
```


At initialization the context key is passed.
Example of initialization:
```python
timestamp = enumeration_key_gen("this-is-an-enumeration-key")
```

Whenever you want to get the value just do it as if it were an IntergerField.
