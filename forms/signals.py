import os

from django.db import models
from django.db.models.fields.files import FieldFile
from django.dispatch import receiver

from forms.models.form import Attachment


@receiver(models.signals.post_delete, sender=Attachment)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.attachment:
        if os.path.isfile(instance.attachment.path):
            os.remove(instance.attachment.path)


@receiver(models.signals.pre_save, sender=Attachment)
def auto_delete_file_on_change(sender, instance: Attachment, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file: FieldFile = Attachment.objects.get(pk=instance.pk).attachment
    except Attachment.DoesNotExist:
        return False

    if not old_file:
        # FieldFile might exist, but doesn't reference a file anymore
        # --> no need to delete anything
        return False

    new_file: FieldFile = instance.attachment
    if not old_file == new_file:
        # Attachment was changed --> delete the previous attachment file
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
