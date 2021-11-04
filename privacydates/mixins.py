class VanishingDateMixIn():
    """The VanishingMixIn is used to register Signals for deletion
     events, so all registered VanishingDateTime will be deleted.
    Inherit it in every class/Model where VanishingDateTime is used.
    Otherwise the VanishingDateTime-Instances are not registered and
     therefore not deleted, when there "parent"-Class was deleted.
    """
    # The class is supposed to be empty,
    # as its only use is to track its subclasses in apps.py



