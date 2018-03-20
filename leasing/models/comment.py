from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import ugettext_lazy as _

from users.models import User

from .mixins import NameModel, TimeStampedSafeDeleteModel


class CommentTopic(NameModel):
    """
    In Finnish: Aihe
    """
    pass


class Comment(TimeStampedSafeDeleteModel):
    """
    In Finnish: Kommentti
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='comments',
                              on_delete=models.PROTECT)

    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.PROTECT)

    topic = models.ForeignKey(CommentTopic, verbose_name=_("Topic"), on_delete=models.PROTECT)

    # In Finnish: Kommentti
    text = models.TextField(verbose_name=_("Text"), null=True, blank=True)

    # In Finnish: Arkistoitu
    is_archived = models.BooleanField(verbose_name=_("Is archived"), default=False)


auditlog.register(Comment)
