from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class PrivacydatesConfig(AppConfig):
    name = 'privacydates'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from .signals import delete_datetime_of_deleted_parent, event_creator_signal_receiver
        from .mixins import VanishingDateMixIn
        from .models import VanishingDateTime

        # Register post-save-signal for VanishingDateTime
        # to start creation of vanishing events
        post_save.connect(event_creator_signal_receiver, sender=VanishingDateTime)

        # Register post_delete-Signal for all Subclasses of VanishingDateMixin
        for sub_class in VanishingDateMixIn.__subclasses__():
            post_delete.connect(delete_datetime_of_deleted_parent,
                                sender=sub_class,
                                dispatch_uid=str(sub_class))





