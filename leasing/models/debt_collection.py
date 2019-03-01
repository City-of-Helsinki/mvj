import io

from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from docxtpl import DocxTemplate

from field_permissions.registry import field_permissions
from leasing.models.mixins import TimeStampedSafeDeleteModel
from users.models import User


def get_collection_letter_file_upload_to(instance, filename):
    return '/'.join(['collection_letters', str(instance.lease.id), filename])


class CollectionLetter(TimeStampedSafeDeleteModel):
    """
    In Finnish: Perintäkirje
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='collection_letters',
                              on_delete=models.PROTECT)

    # In Finnish: Tiedosto
    file = models.FileField(upload_to=get_collection_letter_file_upload_to, verbose_name=_("File"), blank=False,
                            null=False)

    # In Finnish: Lataaja
    uploader = models.ForeignKey(User, verbose_name=_("Uploader"), on_delete=models.PROTECT)

    # In Finnish: Latausaika
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time uploaded"))

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Collection letter")
        verbose_name_plural = pgettext_lazy("Model name", "Collection letters")
        ordering = ['-uploaded_at']


class CollectionLetterTemplate(TimeStampedSafeDeleteModel):
    """
    In Finnish: Perintäkirjepohja
    """
    name = models.CharField(verbose_name=_("Name"), max_length=255)
    file = models.FileField(upload_to='collection_letter_templates/', verbose_name=_("File"), blank=False, null=False)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Collection letter template")
        verbose_name_plural = pgettext_lazy("Model name", "Collection letter templates")
        ordering = ['name']

    def __str__(self):
        return self.name

    def render_document(self, data):
        doc = DocxTemplate(self.file.path)
        doc.render(data)
        output = io.BytesIO()
        doc.save(output)

        return output.getvalue()


class CollectionNote(TimeStampedSafeDeleteModel):
    """
    In Finnish: Huomautus (perintä)
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='collection_notes',
                              on_delete=models.PROTECT)

    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.PROTECT)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Collection letter note")
        verbose_name_plural = pgettext_lazy("Model name", "Collection letter notes")
        ordering = ['-created_at']


def get_collection_court_decision_file_upload_to(instance, filename):
    return '/'.join(['court_decisions', str(instance.lease.id), filename])


class CollectionCourtDecision(TimeStampedSafeDeleteModel):
    """
    In Finnish: Oikeuden päätös
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='collection_court_decisions',
                              on_delete=models.PROTECT)

    # In Finnish: Tiedosto
    file = models.FileField(upload_to=get_collection_court_decision_file_upload_to, verbose_name=_("File"), blank=False,
                            null=False)

    # In Finnish: Päätöspäivämäärä
    decision_date = models.DateField(verbose_name=_("Decision date"), null=True, blank=True)

    # In Finnish: Huomautus
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    # In Finnish: Lataaja
    uploader = models.ForeignKey(User, verbose_name=_("Uploader"), on_delete=models.PROTECT)

    # In Finnish: Latausaika
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time uploaded"))

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Collection court decision")
        verbose_name_plural = pgettext_lazy("Model name", "Collection court decisions")
        ordering = ['-uploaded_at']


class InterestRate(models.Model):
    """
    In Finnish: Korko
    """
    start_date = models.DateField(verbose_name=_("Start date"))
    end_date = models.DateField(verbose_name=_("End date"))
    # In Finnish: Viitekorko
    reference_rate = models.DecimalField(verbose_name=_("Reference rate"), max_digits=10, decimal_places=2)
    # In Finnish: Viivästyskorko
    penalty_rate = models.DecimalField(verbose_name=_("Penalty rate"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Interest rate")
        verbose_name_plural = pgettext_lazy("Model name", "Interest rates")

    def __str__(self):
        return '{} - {}'.format(self.start_date, self.end_date)


auditlog.register(CollectionLetter)
auditlog.register(CollectionLetterTemplate)
auditlog.register(CollectionNote)
auditlog.register(CollectionCourtDecision)
auditlog.register(InterestRate)

field_permissions.register(CollectionLetter, exclude_fields=['lease'])
field_permissions.register(CollectionNote, exclude_fields=['lease'])
field_permissions.register(CollectionCourtDecision, exclude_fields=['lease'])
