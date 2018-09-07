from auditlog.registry import auditlog
from django.contrib.gis.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import InfillDevelopmentCompensationState
from leasing.models.decision import DecisionMaker
from users.models import User

from .mixins import TimeStampedSafeDeleteModel


class LandUseAgreementSubject(TimeStampedSafeDeleteModel):
    """
    In Finnish: Kohde
    """


class LandUseAgreementParty(TimeStampedSafeDeleteModel):
    """
    In Finnish: Osapuoli
    """


class LandUseAgreement(TimeStampedSafeDeleteModel):
    """
    In Finnish: Maankäyttösopimus
    """
    # In Finnish: Nimi
    name = models.CharField(verbose_name=_("Name"), null=True, blank=True, max_length=255)

    # In Finnish: Valmistelija
    preparer = models.ForeignKey(User, verbose_name=_("Preparer"), null=True, blank=True, on_delete=models.PROTECT)

    # In Finnish: Arvioitu toteutumisvuosi
    estimated_completion_year = models.PositiveSmallIntegerField(verbose_name=_("Estimated completion year"), null=True,
                                                                 blank=True)

    # In Finnish: Arvioitu esittelyvuosi
    estimated_presentation_year = models.PositiveSmallIntegerField(verbose_name=_("Estimated presentation year"),
                                                                   null=True, blank=True)

    # In Finnish: Hankealue
    project_area = models.CharField(verbose_name=_("Project area"), null=True, blank=True, max_length=255)

    # In Finnish: Asemakaavan diaarinumero
    detailed_plan_reference_number = models.CharField(verbose_name=_("Detailed plan reference number"), null=True,
                                                      blank=True, max_length=255)

    # In Finnish: Asemakaavan nro.
    detailed_plan_identifier = models.CharField(verbose_name=_("Detailed plan identifier"), max_length=255, null=True,
                                                blank=True)

    # In Finnish: Asemakaavan käsittelyvaihe
    detailed_plan_state = EnumField(InfillDevelopmentCompensationState, verbose_name=_("Detailed plan state"),
                                    null=True, blank=True, max_length=30)

    # In Finnish: Päättäjä
    detailed_plan_decision_maker = models.ForeignKey(DecisionMaker, verbose_name=_("Detailed plan decision maker"),
                                                     related_name="land_use_agreements", null=True, blank=True,
                                                     on_delete=models.PROTECT)
    # In Finnish: Vuokrasopimuksen muutospvm
    lease_contract_change_date = models.DateField(verbose_name=_("Lease contract change date"), null=True, blank=True)

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    leases = models.ManyToManyField('leasing.Lease', through='leasing.InfillDevelopmentCompensationLease',
                                    related_name='leases')

    # In Finnish: Alue
    geometry = models.MultiPolygonField(srid=4326, verbose_name=_("Geometry"), null=True, blank=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Land use agreement")
        verbose_name_plural = pgettext_lazy("Model name", "Land use agreements")

    def __str__(self):
        return self.name if self.name else 'Land use agreement #{}'.format(self.id)


class LandUseAgreementDecision(TimeStampedSafeDeleteModel):
    """
    In Finnish: Maankäyttösopimuspäätös
    """
    land_use_agreement = models.ForeignKey(LandUseAgreement, verbose_name=_("Land use agreement"),
                                           related_name='decisions', on_delete=models.PROTECT)

    # In Finnish: Diaarinumero
    reference_number = models.CharField(verbose_name=_("Reference number"), null=True, blank=True, max_length=255)

    # In Finnish: Päättäjä
    decision_maker = models.ForeignKey(DecisionMaker, verbose_name=_("Decision maker"),
                                       related_name="land_use_agreement_decisions", null=True, blank=True,
                                       on_delete=models.PROTECT)

    # In Finnish: Päätöspäivämäärä
    decision_date = models.DateField(verbose_name=_("Decision date"), null=True, blank=True)

    # In Finnish: Pykälä
    section = models.CharField(verbose_name=_("Section"), null=True, blank=True, max_length=255)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Land use agreement decision")
        verbose_name_plural = pgettext_lazy("Model name", "Land use agreement decisions")


def get_attachment_file_upload_to(instance, filename):
    return '/'.join(['lua_attachments', str(instance.land_use_agreement.id), filename])


class LandUseAgreementAttachment(TimeStampedSafeDeleteModel):
    """
    In Finnish: Maankäyttösopimusliitetiedosto
    """
    land_use_agreement = models.ForeignKey(LandUseAgreement, verbose_name=_("Land use agreement"),
                                           related_name='attachments', on_delete=models.PROTECT)

    # In Finnish: Tiedosto
    file = models.FileField(upload_to=get_attachment_file_upload_to, blank=False, null=False)

    # In Finnish: Lataaja
    uploader = models.ForeignKey(User, verbose_name=_("Uploader"), on_delete=models.PROTECT)

    # In Finnish: Latausaika
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time uploaded"))

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Land use agreement attachment")
        verbose_name_plural = pgettext_lazy("Model name", "Land use agreement attachments")


auditlog.register(LandUseAgreement)
