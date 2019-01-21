from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.models import Invoice, Lease, Tenant
from users.serializers import UserSerializer

from ..models.debt_collection import CollectionCourtDecision, CollectionLetter, CollectionLetterTemplate, CollectionNote
from .utils import FileSerializerMixin, InstanceDictPrimaryKeyRelatedField


class CollectionCourtDecisionSerializer(FileSerializerMixin, FieldPermissionsSerializerMixin,
                                        serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    uploader = UserSerializer()
    file = serializers.SerializerMethodField('get_file_url')
    filename = serializers.SerializerMethodField('get_file_filename')

    class Meta:
        model = CollectionCourtDecision
        fields = ('id', 'lease', 'file', 'filename', 'uploader', 'uploaded_at')
        download_url_name = 'collectioncourtdecision-download'

    def override_permission_check_field_name(self, field_name):
        if field_name == 'filename':
            return 'file'

        return field_name


class CollectionCourtDecisionCreateUpdateSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    uploader = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CollectionCourtDecision
        fields = ('id', 'lease', 'file', 'uploader', 'uploaded_at')
        read_only_fields = ('uploaded_at',)


class CollectionLetterSerializer(FileSerializerMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    uploader = UserSerializer()
    file = serializers.SerializerMethodField('get_file_url')
    filename = serializers.SerializerMethodField('get_file_filename')

    class Meta:
        model = CollectionLetter
        fields = ('id', 'lease', 'file', 'filename', 'uploader', 'uploaded_at')
        download_url_name = 'collectionletter-download'

    def override_permission_check_field_name(self, field_name):
        if field_name == 'filename':
            return 'file'

        return field_name


class CollectionLetterCreateUpdateSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    uploader = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CollectionLetter
        fields = ('id', 'lease', 'file', 'uploader', 'uploaded_at')
        read_only_fields = ('uploaded_at',)


class CollectionLetterTemplateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = CollectionLetterTemplate
        fields = ('id', 'name')


class CollectionNoteSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    user = UserSerializer(read_only=True)

    class Meta:
        model = CollectionNote
        fields = '__all__'


class CollectionNoteCreateUpdateSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CollectionNote
        fields = '__all__'


class CreateCollectionLetterDocumentSerializer(serializers.Serializer):
    lease = InstanceDictPrimaryKeyRelatedField(instance_class=Lease, queryset=Lease.objects.all())
    template = InstanceDictPrimaryKeyRelatedField(instance_class=CollectionLetterTemplate,
                                                  queryset=CollectionLetterTemplate.objects.all())
    collection_charge = serializers.DecimalField(max_digits=12, decimal_places=2)
    tenants = serializers.PrimaryKeyRelatedField(many=True, queryset=Tenant.objects.all())
    invoices = serializers.PrimaryKeyRelatedField(many=True, queryset=Invoice.objects.all())

    # TODO: Validate tenant and invoices
