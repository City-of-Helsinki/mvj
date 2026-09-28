import factory
from django.contrib.contenttypes.models import ContentType

from file_operations.models.filescan import FileScanStatus
from plotsearch.tests.factories import AreaSearchAttachmentFactory


class FileScanStatusFactory(factory.django.DjangoModelFactory):
    content_object = factory.SubFactory(AreaSearchAttachmentFactory)

    @factory.lazy_attribute
    def content_type(self):
        return ContentType.objects.get_for_model(self.content_object)

    @factory.lazy_attribute
    def object_id(self):
        return self.content_object.id

    class Meta:
        model = FileScanStatus
