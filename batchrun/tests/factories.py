import factory

from batchrun.models import Command, Job, JobRun, JobRunLog


class CommandFactory(factory.django.DjangoModelFactory):
    type = "django-manage"

    class Meta:
        model = Command


class JobFactory(factory.django.DjangoModelFactory):
    command = factory.SubFactory(CommandFactory)

    class Meta:
        model = Job


class JobRunFactory(factory.django.DjangoModelFactory):
    job = factory.SubFactory(JobFactory)

    class Meta:
        model = JobRun


class JobRunLogFactory(factory.django.DjangoModelFactory):
    run = factory.SubFactory(JobRunFactory)

    class Meta:
        model = JobRunLog
