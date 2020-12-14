from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..utils import clone_object, generate_unique_identifier


class Form(models.Model):

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_template = models.BooleanField(default=False)

    title = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time created"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("Time modified"))

    def clone(self):
        assert self.is_template  # Only templates can be clone
        return clone_object(self)


class Section(models.Model):

    title = models.CharField(max_length=255)
    identifier = models.SlugField()
    visible = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    add_new_allowed = models.BooleanField(default=False)
    add_new_text = models.CharField(max_length=255)

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="subsections",
    )
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="sections")

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


class FieldType(models.Model):

    name = models.CharField(max_length=255)
    identifier = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.identifier:
            max_length = self._meta.get_field("identifier").max_length
            self.identifier = generate_unique_identifier(
                FieldType, "identifier", self.name, max_length
            )
        super(FieldType, self).save(*args, **kwargs)


class Field(models.Model):

    label = models.CharField(max_length=255)
    hint_text = models.CharField(max_length=255)
    identifier = models.SlugField()
    enabled = models.BooleanField(default=True)
    required = models.BooleanField(default=False)
    validation = models.CharField(max_length=255)
    action = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)

    type = models.ForeignKey(FieldType, on_delete=models.PROTECT)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

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


class Choice(models.Model):

    text = models.CharField(max_length=255)
    value = models.CharField(max_length=50)
    action = models.CharField(max_length=255)
    has_text_input = models.BooleanField(default=False)

    field = models.ForeignKey(Field, on_delete=models.CASCADE)
