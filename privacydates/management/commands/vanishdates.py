from django.core.management.base import BaseCommand

from ...vanish import update_vanishing


class Command(BaseCommand):
    """Management command to execute the vanishing_updater with
     external programms, like cron, for manual or automated usage.
    """
    help = 'Runs a task that executes all scheduled vanishing_dates'

    def handle(self, *args, **options):
        update_vanishing()
        self.stdout.write(self.style.SUCCESS('Vanishing executed'))
