from django.apps import AppConfig
from django.db.models.signals import post_delete


class PrivacydatesConfig(AppConfig):
    name = 'privacydates'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from .mixins import VanishingDateMixIn
        from .signals import delete_datetime_of_deleted_parent

        # Register post_delete-Signal for all Subclasses of VanishingDateMixin
        for sub_class in VanishingDateMixIn.__subclasses__():
            post_delete.connect(delete_datetime_of_deleted_parent,
                                sender=sub_class,
                                dispatch_uid=str(sub_class))





