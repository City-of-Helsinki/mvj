from django.db import models
from django.db.models.fields.json import JSONField
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField
from helsinki_gdpr.models import SerializableMixin

from filescan.mixins import FileScanMixin
from users.models import User
from utils.models.fields import PrivateFileField

from ..enums import ApplicantType, FormState, SectionType
from ..utils import clone_object, generate_unique_identifier


class Form(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_template = models.BooleanField(default=False)
    is_area_form = models.BooleanField(default=False)
    state = EnumField(FormState, max_length=30, default=FormState.WORK_IN_PROGRESS)

    title = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time created"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("Time modified"))

    def clone(self):
        assert self.is_template  # Only templates can be clone
        return clone_object(self)

    def __str__(self):
        return self.name

    recursive_get_related_skip_relations = [
        "section",
        "answer",
        "areasearch",
        "plotsearch",
    ]


class Section(models.Model):
    title = models.CharField(max_length=255)
    identifier = models.SlugField()
    visible = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    add_new_allowed = models.BooleanField(default=False)
    add_new_text = models.CharField(max_length=255, null=True, blank=True)
    show_duplication_check = models.BooleanField(default=True)

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="subsections",
    )
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="sections")
    type = EnumField(SectionType, max_length=30, default=SectionType.SHOW_ALWAYS)
    applicant_type = EnumField(ApplicantType, max_length=30, default=ApplicantType.BOTH)

    class Meta:
        ordering = ["sort_order"]
        unique_together = (
            "form",
            "identifier",
        )

    def save(self, *args, **kwargs):
        if not self.id or not self.identifier:
            max_length = self._meta.get_field("identifier").max_length
            self.identifier = generate_unique_identifier(
                Section,
                "identifier",
                self.title,
                max_length,
                filter={"form_id": self.form.id},
            )
        super(Section, self).save(*args, **kwargs)

    @staticmethod
    def get_root(section):
        if section.parent is not None:
            return Section.get_root(section.parent)
        return section

    def __str__(self):
        return self.title

    recursive_get_related_skip_relations = [
        "field",
    ]


class Field(models.Model):
    FIELD_TYPES = (
        ("textbox", _("Tekstikenttä")),
        ("textarea", _("Tekstialue")),
        ("dropdown", _("Alasvetovalikko")),
        ("checkbox", _("Valintaruutu")),
        ("radiobutton", _("Radiopainike")),
        ("radiobuttoninline", _("Radiopainike linjassa")),
        ("uploadfiles", _("Lataa tiedosto")),
        ("fractional", _("Murtoluku")),
    )
    label = models.CharField(max_length=255)
    hint_text = models.CharField(max_length=1024, null=True, blank=True)
    identifier = models.SlugField()
    enabled = models.BooleanField(default=True)
    required = models.BooleanField(default=False)
    validation = models.CharField(max_length=255, null=True, blank=True)
    action = models.CharField(max_length=255, null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    default_value = models.CharField(max_length=512, null=True, blank=True)
    type = models.CharField(max_length=255, choices=FIELD_TYPES)
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="fields"
    )

    class Meta:
        ordering = ["sort_order"]
        unique_together = (
            "section",
            "identifier",
        )

    def save(self, *args, **kwargs):
        if not self.identifier:
            max_length = self._meta.get_field("identifier").max_length
            self.identifier = generate_unique_identifier(
                Field,
                "identifier",
                self.label,
                max_length,
                filter={"section_id": self.section.id},
            )
        super(Field, self).save(*args, **kwargs)

    def __str__(self):
        return self.label

    recursive_get_related_skip_relations = [
        "choice",
        "attachment",
        "entry",
    ]


class Choice(models.Model):
    text = models.CharField(max_length=255)
    value = models.CharField(max_length=50)
    action = models.CharField(max_length=255, null=True, blank=True)
    has_text_input = models.BooleanField(default=False)

    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name="choices")

    recursive_get_related_skip_relations = []


class Answer(models.Model):
    """
    Model for saving form inputs
    """

    form = models.ForeignKey(Form, on_delete=models.PROTECT)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now=True)
    ready = models.BooleanField(default=False)

    recursive_get_related_skip_relations = [
        "form",
        "user",
        "attachment",
        "areasearch",
        "targetstatus",
        "entrysection",
        "answeropeningrecord",
    ]


class AnswerOpeningRecord(models.Model):
    """
    In Finnish: Avauspöytäkirja
    """

    time_stamp = models.DateTimeField(auto_now=True)
    openers = models.ManyToManyField(User, related_name="+")
    note = models.TextField(blank=True, null=True)

    answer = models.OneToOneField(
        Answer, on_delete=models.CASCADE, related_name="opening_record"
    )

    recursive_get_related_skip_relations = [
        "answeropeningrecord_openers",
    ]


def get_attachment_file_upload_to(instance, filename):
    return "/".join(
        [
            "plot_search_attachments",
            str(instance.field.id),
            str(instance.user.username),
            filename,
        ]
    )


class Attachment(FileScanMixin, SerializableMixin, models.Model):
    name = models.CharField(max_length=255)
    attachment = PrivateFileField(upload_to=get_attachment_file_upload_to)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time created"))
    path = models.TextField(null=True, blank=True)

    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    # GDPR API
    serialize_fields = (
        {"name": "name"},
        {"name": "attachment"},
        {"name": "created_at"},
    )

    recursive_get_related_skip_relations = [
        "user",
    ]


class EntrySection(models.Model):
    metadata = JSONField(null=True)
    identifier = models.SlugField()

    answer = models.ForeignKey(
        Answer, on_delete=models.CASCADE, related_name="entry_sections", null=True
    )

    recursive_get_related_skip_relations = [
        "entry",
    ]


class Entry(models.Model):
    """
    Model for saving Answer entries
    """

    entry_section = models.ForeignKey(
        EntrySection, on_delete=models.CASCADE, related_name="entries", null=True
    )
    field = models.ForeignKey(Field, on_delete=models.PROTECT)
    value = models.TextField()
    extra_value = models.TextField(blank=True, null=True)
    path = models.TextField()

    recursive_get_related_skip_relations = [
        "field",
    ]


from forms.signals import *  # noqa: E402 F403 F401
