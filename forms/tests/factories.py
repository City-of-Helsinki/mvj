import factory

from forms.models import Answer, Choice, Entry, Field, Form, Section
from forms.models.form import Attachment, EntrySection
from users.tests.factories import UserFactory


class FormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Form


class SectionFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = Section


class FieldFactory(factory.django.DjangoModelFactory):
    section = factory.SubFactory(SectionFactory)

    class Meta:
        model = Field


class EntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Entry


class EntrySectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EntrySection


class AnswerFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = Answer


class AttachmentFactory(factory.django.DjangoModelFactory):
    field = factory.SubFactory(FieldFactory)

    class Meta:
        model = Attachment


class ChoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Choice
