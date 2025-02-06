from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from file_operations.models.filescan import FileScanStatus
from file_operations.private_files import PrivateFieldFile, PrivateFileField


class Command(BaseCommand):
    help = "Create FileScanStatus objects for files that don't have one"

    def handle(self, *args, **options):

        # Iterate through all models in the project
        for model in apps.get_models():
            with transaction.atomic():
                # Iterate through all fields in the model
                for field in model._meta.get_fields():
                    if isinstance(field, PrivateFileField):
                        # Traverse all instances of the model
                        for instance in model.objects.all():
                            field_file: PrivateFieldFile = getattr(instance, field.name)
                            if field_file and field_file.name:
                                # Check if a FileScanStatus object exists for this file
                                content_type = ContentType.objects.get_for_model(
                                    instance
                                )
                                if not FileScanStatus.objects.filter(
                                    content_type=content_type,
                                    object_id=instance.pk,
                                ).exists():
                                    # Create a FileScanStatus object for the file
                                    FileScanStatus.objects.create(
                                        content_object=instance,
                                        content_type=content_type,
                                        object_id=instance.pk,
                                        filepath=field_file.path,
                                        filefield_name=field.name,
                                    )
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"Created FileScanStatus for {field_file.name}"
                                        )
                                    )
