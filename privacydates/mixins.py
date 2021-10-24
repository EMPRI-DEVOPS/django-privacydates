class AnnihilationMixIn():
    """The AnnihilationMixIn is used to register Signals for deletion
     events, so all included DateTimeAnnihilations will be deleted.
    Inherit it in every class/Model where DateTimeAnnihilation is used.
    Otherwise the DateTimeAnnihilation-Instances are not deleted,
     when there "parent"-Class was deleted.
    """
    # The class is supposed to be empty,
    # as it is only used to track its subclasses in apps.py



