import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models as gmodels
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import EnumField
from helsinki_gdpr.models import SerializableMixin
from rest_framework.serializers import ValidationError
from safedelete.models import SOFT_DELETE, SafeDeleteModel

from field_permissions.registry import field_permissions
from forms.models import Answer, Form
from forms.models.form import EntrySection
from forms.utils import get_answer_worksheet, get_area_search_answer_worksheet
from leasing.enums import PlotSearchTargetType
from leasing.models import Financing, Hitas, Lease, Management, ServiceUnit
from leasing.models.mixins import NameModel, TimeStampedSafeDeleteModel
from plotsearch.enums import (
    AreaSearchLessor,
    AreaSearchState,
    DeclineReason,
    InformationCheckName,
    InformationState,
    RelatedPlotApplicationContentType,
    SearchClass,
    SearchStage,
)
from plotsearch.utils import map_intended_use_to_lessor
from users.models import User


class PlotSearchType(NameModel):
    """
    In Finnish: Hakutyyppi
    """

    ordering = models.PositiveSmallIntegerField(default=0, db_index=True)

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plot search type")
        verbose_name_plural = pgettext_lazy("Model name", "Plot search types")
        ordering = ["ordering", "name"]

    recursive_get_related_skip_relations = [
        "plotsearch_subtype",
    ]


class PlotSearchSubtype(NameModel):
    """
    In Finnish: Haun alatyyppi
    """

    plot_search_type = models.ForeignKey(PlotSearchType, on_delete=models.CASCADE)
    show_district = models.BooleanField(default=False)
    target_selection = models.BooleanField(default=False)
    require_opening_record = models.BooleanField(default=False)
    ordering = models.PositiveSmallIntegerField(default=0, db_index=True)

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plot search subtype")
        verbose_name_plural = pgettext_lazy("Model name", "Plot search subtypes")
        ordering = ["ordering", "name"]

    recursive_get_related_skip_relations = [
        "plotsearch",
    ]


class PlotSearchStage(NameModel):
    """
    In Finnish: Haun vaihe
    """

    # In Finnish: Haun vaihe
    stage = EnumField(
        enum=SearchStage,
        default=SearchStage.IN_PREPARATION,
        max_length=30,
        null=True,
        blank=True,
    )

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plot search stage")
        verbose_name_plural = pgettext_lazy("Model name", "Plot search stages")

    recursive_get_related_skip_relations = [
        "plotsearch",
    ]


class PlotSearch(TimeStampedSafeDeleteModel, NameModel):
    """
    In Finnish: Tonttihaku
    """

    # In Finnish: Valmistelijat
    preparers = models.ManyToManyField(
        User,
        verbose_name=_("Preparer"),
        related_name="+",
        blank=True,
    )

    # In Finnish: Haun tyyppi
    subtype = models.ForeignKey(
        PlotSearchSubtype,
        verbose_name=_("Subtype"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Alkuaika
    begin_at = models.DateTimeField(verbose_name=_("Begin at"), null=True, blank=True)

    # In Finnish: Loppuaika
    end_at = models.DateTimeField(verbose_name=_("End at"), null=True, blank=True)

    # In Finnish: Haun luokittelu
    search_class = EnumField(enum=SearchClass, max_length=30, null=True, blank=True)

    # In Finnish: Haun vaihe
    stage = models.ForeignKey(
        PlotSearchStage,
        verbose_name=_("Stage"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Lomake
    form = models.OneToOneField(Form, on_delete=models.SET_NULL, null=True)

    decisions = models.ManyToManyField(
        "leasing.Decision", related_name="plot_searches", blank=True
    )

    recursive_get_related_skip_relations = [
        "plotsearch_decisions",
        "plotsearchtarget",
        "plotsearch_preparers",
        "form",
        "related_plot_applications",
    ]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Plot search")
        verbose_name_plural = pgettext_lazy("Model name", "Plot searches")

    def __str__(self):
        return "Plot search #{}".format(self.id)


class PlotSearchTarget(models.Model):
    """
    In Finnish: Tonttihaun kohde
    """

    # In Finnish: Tonttihaku
    plot_search = models.ForeignKey(
        PlotSearch, on_delete=models.CASCADE, related_name="plot_search_targets"
    )

    # In Finnish: Kaavayksikkö
    plan_unit = models.OneToOneField(
        "leasing.PlanUnit", on_delete=models.CASCADE, null=True, blank=True
    )

    custom_detailed_plan = models.OneToOneField(
        "leasing.CustomDetailedPlan", on_delete=models.CASCADE, null=True, blank=True
    )

    reservation_identifier = models.OneToOneField(
        "leasing.Lease",
        related_name="plot_search_target",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # In finnish: Hakemukset
    answers = models.ManyToManyField(
        Answer, related_name="targets", blank=True, through="TargetStatus"
    )

    # In Finnish: Tonttihaun kohteet: Haettavat kohteet, menettelyvaraus ja suoravaraus
    target_type = EnumField(
        PlotSearchTargetType,
        verbose_name=_("Target type"),
        max_length=30,
    )

    recursive_get_related_skip_relations = [
        "targetstatus",
        "favouritetarget",
        "directreservationlink_targets",
        "targetinfolink" "lease",
        "planunit",
        "customdetailedplan",
    ]

    def identifier(self):
        if self.plan_unit is not None:
            return self.plan_unit.identifier
        if self.custom_detailed_plan is not None:
            return self.custom_detailed_plan.identifier
        return ""

    def save(self, *args, **kwargs):
        self.clean()
        return super(PlotSearchTarget, self).save(*args, **kwargs)

    def clean(self):
        if self.plan_unit is not None and self.custom_detailed_plan is not None:
            raise ValidationError
        if self.plan_unit is None and self.custom_detailed_plan is None:
            raise ValidationError


class InformationCheck(models.Model):
    """
    In Finnish: Lisätiedon tila
    """

    # In Finnish: Nimi
    name = EnumField(enum=InformationCheckName, max_length=30)

    # In Finnish: Käsittelijä
    preparer = models.ForeignKey(
        User,
        verbose_name=_("Preparer"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Vastauksen osio
    entry_section = models.ForeignKey(EntrySection, on_delete=models.CASCADE)

    # In Finnish: Tila
    state = EnumField(
        enum=InformationState, max_length=30, default=InformationState.NOT_CHECKED
    )

    # In Finnish: Kommentti
    comment = models.TextField(null=True, blank=True)

    # In Finnish: Luontiaika
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time created"))
    # In Finnish: Muokkausaika
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("Time modified"))

    recursive_get_related_skip_relations = [
        "user",
    ]


def target_status_id_generator():
    year = str(timezone.now().year)[2:4]

    beginning_str = "TH-{}".format(year)
    latest_target_status_with_id = TargetStatus.objects.filter(
        application_identifier__startswith=beginning_str
    )

    if not latest_target_status_with_id.exists():
        return "{}-00001".format(beginning_str)

    application_id = latest_target_status_with_id.last().application_identifier
    identifier = int(application_id.split("-")[2])
    identifier += 1
    return "{}-{:05d}".format(beginning_str, identifier)


class TargetStatus(models.Model):
    # In Finnish: Tonttihaun kohde
    plot_search_target = models.ForeignKey(
        PlotSearchTarget, related_name="statuses", blank=True, on_delete=models.CASCADE
    )
    # In Finnish: Hakemus
    answer = models.ForeignKey(
        Answer, related_name="statuses", on_delete=models.CASCADE
    )

    # In Finnish: Vuokrauksen osuuden osoittaja
    share_of_rental_indicator = models.IntegerField(null=True, blank=True)
    # In Finnish: Vuokrauksen osuuden nimittäjä
    share_of_rental_denominator = models.IntegerField(null=True, blank=True)

    # In Finnish: Esitetään varattavaksi
    reserved = models.BooleanField(default=False)
    # In Finnish: Hakijalle lisätty kohde
    added_target_to_applicant = models.BooleanField(default=False)
    # In Finnish: Neuvottelu päivämäärä
    counsel_date = models.DateTimeField(null=True, blank=True)
    # In Finnish: Hylkäyksen syy
    decline_reason = EnumField(DeclineReason, max_length=30, null=True, blank=True)

    reservation_conditions = ArrayField(
        base_field=models.TextField(), blank=True, null=True
    )

    # In Finnish: Perustelut
    arguments = models.TextField(null=True, blank=True)

    # In Finnish: Hakmuksen tunniste
    application_identifier = models.CharField(
        max_length=255, unique=True, default=target_status_id_generator
    )

    # In Finnish: Vuokraus
    lease = models.ForeignKey(
        Lease,
        related_name="target_statuses",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    recursive_get_related_skip_relations = [
        "related_plot_applications",
        "meetingmemo",
        "proposedfinancingmanagement",
        "lease",
    ]

    def target_status_get_xlsx_page(self, worksheet, row):
        return get_answer_worksheet(self, worksheet, row)


class ProposedFinancingManagement(models.Model):
    # In Finnish: Ehdotettu rahoitusmuoto
    proposed_financing = models.ForeignKey(
        Financing,
        verbose_name=_("Form of financing"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Ehdotettu hallintamuoto
    proposed_management = models.ForeignKey(
        Management,
        verbose_name=_("Form of management"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    # In Finnish: Hitas
    hitas = models.ForeignKey(
        Hitas,
        verbose_name=_("Hitas"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Hakemuksen käsittelytiedot
    target_status = models.ForeignKey(
        TargetStatus, on_delete=models.CASCADE, related_name="proposed_managements"
    )

    recursive_get_related_skip_relations = [
        "hitas",
        "financing",
        "management",
    ]


def get_meeting_memo_file_upload_to(instance, filename):
    if instance.target_status.counsel_date is not None:
        return "/".join(
            [
                "meeting_memos",
                str(instance.target_status.counsel_date.date().isoformat()),
                filename,
            ]
        )
    else:
        return "/".join(
            [
                "meeting_memos",
                str(timezone.now().date().isoformat()),
                filename,
            ]  # noqa: E231
        )


class MeetingMemo(models.Model):
    # In Finnish: Kokousmuistio
    name = models.CharField(max_length=255)
    meeting_memo = models.FileField(
        upload_to=get_meeting_memo_file_upload_to, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time created"))

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="meeting_memos"
    )

    # In Finnish: Hakemuksen käsittelytiedot
    target_status = models.ForeignKey(
        TargetStatus, on_delete=models.CASCADE, related_name="meeting_memos"
    )

    recursive_get_related_skip_relations = [
        "user",
    ]


class Favourite(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_at = models.DateTimeField(auto_now=True)

    recursive_get_related_skip_relations = [
        "favouritetarget",
        "user",
    ]


class FavouriteTarget(models.Model):
    favourite = models.ForeignKey(
        Favourite, on_delete=models.CASCADE, related_name="targets"
    )
    plot_search_target = models.ForeignKey(PlotSearchTarget, on_delete=models.CASCADE)

    recursive_get_related_skip_relations = []


class AreaSearchIntendedUse(SerializableMixin, SafeDeleteModel, NameModel):
    _safedelete_policy = SOFT_DELETE

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Area search intended use")
        verbose_name_plural = pgettext_lazy("Model name", "Area search intended uses")
        ordering = ["name"]

    # GDPR API
    serialize_fields = ({"name": "name"},)

    recursive_get_related_skip_relations = [
        "areasearch",
    ]


def areasearch_id_generator():
    year = str(timezone.now().year)[2:4]

    beginning_str = "MVJ-{}".format(year)
    latest_area_search_with_id = AreaSearch.objects.filter(
        identifier__startswith=beginning_str
    )

    if not latest_area_search_with_id.exists():
        return "{}-00001".format(beginning_str)

    area_search_id = latest_area_search_with_id.last().identifier
    identifier = int(area_search_id.split("-")[2])
    identifier += 1
    return "{}-{:05d}".format(beginning_str, identifier)


class AreaSearchStatus(models.Model):
    decline_reason = EnumField(DeclineReason, max_length=30, null=True, blank=True)
    preparer_note = models.TextField(blank=True, null=True)

    recursive_get_related_skip_relations = [
        "areasearch",
        "areasearchstatusnote",
    ]


class AreaSearch(SerializableMixin, models.Model):
    # In Finnish: aluehaku

    geometry = gmodels.MultiPolygonField(
        srid=4326, verbose_name=_("Geometry"), null=True, blank=True
    )

    lessor = EnumField(
        enum=AreaSearchLessor,
        verbose_name=_("Lessor"),
        default=None,
        null=True,
        blank=True,
        max_length=30,
    )

    @property
    def lessor_name(self):
        if self.intended_use is not None:
            return map_intended_use_to_lessor(self.intended_use)
        return self.lessor

    description_area = models.TextField(blank=True)

    address = models.CharField(max_length=255, null=True, blank=True)
    district = models.CharField(max_length=255, null=True, blank=True)

    intended_use = models.ForeignKey(AreaSearchIntendedUse, on_delete=models.PROTECT)
    description_intended_use = models.TextField()

    start_date = models.DateTimeField(verbose_name=_("Begin at"), null=True, blank=True)
    end_date = models.DateTimeField(verbose_name=_("End at"), null=True, blank=True)

    received_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Time received")
    )

    identifier = models.CharField(
        max_length=255, unique=True, default=areasearch_id_generator
    )

    state = EnumField(
        AreaSearchState,
        verbose_name=_("Area search state"),
        default=AreaSearchState.RECEIVED,
        max_length=30,
    )

    form = models.ForeignKey(
        Form, on_delete=models.SET_NULL, null=True, related_name="area_searches"
    )
    answer = models.OneToOneField(
        Answer, on_delete=models.CASCADE, null=True, related_name="area_search"
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # In Finnish: Käsittelijä
    preparer = models.ForeignKey(
        User,
        verbose_name=_("Preparer"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    lease = models.ForeignKey(
        Lease,
        related_name="area_searches",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    area_search_status = models.OneToOneField(
        AreaSearchStatus,
        on_delete=models.CASCADE,
        related_name="area_search",
        null=True,
    )

    service_unit = models.ForeignKey(
        ServiceUnit,
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # GDPR API
    serialize_fields = (
        {"name": "address"},
        {"name": "received_date"},
        {"name": "start_date"},
        {"name": "end_date"},
        # plotsearch.AreaSearchAttachment
        {"name": "area_search_attachments"},
        # plotsearch.AreaSearchIntendedUse
        {"name": "intended_use"},
    )

    recursive_get_related_skip_relations = [
        "related_plot_applications",
        "areasearchattachment",
        "user",
        "lease",
        "form",
    ]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Area search")
        verbose_name_plural = pgettext_lazy("Model name", "Area searches")

    def clean(self):
        if not self.description_area and not self.geometry:
            raise ValidationError(
                "Fields description_area and geometry may not be null or blank at the same time."
            )

    def save(self, *args, **kwargs):
        self.clean()
        return super(AreaSearch, self).save(*args, **kwargs)

    def get_xlsx_page(self, worksheet, row):
        return get_area_search_answer_worksheet(self, worksheet, row)


def get_area_search_attachment_upload_to(instance, filename):
    return "/".join(
        [
            "area_search_attachments",
            str(timezone.now().date().isoformat()),
            filename,
        ]  # noqa: E231
    )


class AreaSearchAttachment(SerializableMixin, NameModel):
    attachment = models.FileField(
        upload_to=get_area_search_attachment_upload_to, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time created"))

    user = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="+"
    )

    # In Finnish: Aluehaut
    area_search = models.ForeignKey(
        AreaSearch,
        on_delete=models.CASCADE,
        related_name="area_search_attachments",
        null=True,
        blank=True,
    )

    # GDPR API
    serialize_fields = (
        {"name": "name"},
        {"name": "created_at"},
    )

    recursive_get_related_skip_relations = [
        "user",
    ]


class AreaSearchStatusNote(models.Model):
    note = models.TextField()
    preparer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    time_stamp = models.DateTimeField(auto_created=True)
    area_search_status = models.ForeignKey(
        AreaSearchStatus, on_delete=models.CASCADE, related_name="status_notes"
    )

    recursive_get_related_skip_relations = [
        "user",
    ]


class DirectReservationLink(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    targets = models.ManyToManyField(PlotSearchTarget)

    def get_external_url(self):
        return "{}/suoravaraus/{}".format(settings.PUBLIC_UI_URL, self.uuid)

    recursive_get_related_skip_relations = [
        "directreservationlink_targets",
    ]


class FAQ(models.Model):
    question = models.TextField(unique=True)
    answer = models.TextField()

    @property
    def question_truncate(self):
        return self.question if len(self.question) < 50 else (self.question[:50] + "..")

    @property
    def answer_truncate(self):
        return self.answer if len(self.answer) < 50 else (self.answer[:50] + "..")

    recursive_get_related_skip_relations = []


class RelatedPlotApplication(TimeStampedSafeDeleteModel):
    """
    In Finnish: Liittyvät (tontti/alue)hakemukset
    """

    lease = models.ForeignKey(
        "leasing.Lease",
        related_name="related_plot_applications",
        on_delete=models.CASCADE,
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        # Explicitly limits choice to these models, but can be extended to any model
        limit_choices_to={"model__in": RelatedPlotApplicationContentType.values()},
    )
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    recursive_get_related_skip_relations = [
        "lease",
        "content_type",
    ]


auditlog.register(PlotSearch)
auditlog.register(AreaSearch)
auditlog.register(InformationCheck)
auditlog.register(RelatedPlotApplication)

field_permissions.register(PlotSearch)
field_permissions.register(AreaSearch)
