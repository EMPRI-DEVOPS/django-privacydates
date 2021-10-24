from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class PrivacydatesConfig(AppConfig):
    name = 'privacydates'

    def ready(self):
        from .signals import delete_datetime_of_deleted_parent, event_creator_signal_receiver
        from .mixins import AnnihilationMixIn
        from .models import DateTimeAnnihilation

        # Register post-save-signal for DateTimeAnnihilation
        # to start creation of annihilation events
        post_save.connect(event_creator_signal_receiver, sender=DateTimeAnnihilation)

        # Register post_delete-Signal for all Subclasses of AnnihilationMixin
        for sub_class in AnnihilationMixIn.__subclasses__():
            post_delete.connect(delete_datetime_of_deleted_parent,
                                sender=sub_class,
                                dispatch_uid=str(sub_class))





