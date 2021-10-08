import logging
import sys

from django.core.management.base import BaseCommand

from leasing.models import Rent

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Payable rent calculation"

    def handle(self, *args, **options):  # noqa: C901 TODO
        from auditlog.registry import auditlog

        logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

        verbosity = options.get("verbosity")
        if verbosity == 0:
            logger.setLevel(logging.WARNING)
        elif verbosity >= 2:
            logger.setLevel(logging.DEBUG)

        # Unregister all models from auditlog when importing
        for model in list(auditlog._registry.keys()):
            auditlog.unregister(model)

        for rent in Rent.objects.all().iterator():
            try:
                rent.calculate_payable_rent()
            except Exception as e:
                logger.exception(
                    "Failed to calculate payable rent (%s): %s" % (rent.id, str(e))
                )
                continue
