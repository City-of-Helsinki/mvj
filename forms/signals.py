import os

from django.db import models
from django.dispatch import receiver

from forms.models.form import Attachment


@receiver(models.signals.post_delete, sender=Attachment)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.attachment:
        if os.path.isfile(instance.attachment.path):
            os.remove(instance.attachment.path)


@receiver(models.signals.pre_save, sender=Attachment)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file = Attachment.objects.get(pk=instance.pk).attachment
    except Attachment.DoesNotExist:
        return False

    new_file = instance.attachment
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
