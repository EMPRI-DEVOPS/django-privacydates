from django.core.management.base import BaseCommand

from ...annihilation import annihilation_updater


class Command(BaseCommand):
    """Management command to execute the annihilation_updater with
     external programms, like cron, for manual or automated usage.
    """
    help = 'Runs a task that executes all scheduled annihilations'

    def handle(self, *args, **options):
        annihilation_updater()

        self.stdout.write(self.style.SUCCESS('Annihilation executed'))
