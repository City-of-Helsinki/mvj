from rest_framework import serializers

from users.serializers import UserSerializer

from ..models.debt_collection import CollectionCourtDecision, CollectionLetter, CollectionLetterTemplate, CollectionNote
from .utils import FileSerializerMixin


class CollectionCourtDecisionSerializer(FileSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    uploader = UserSerializer()
    file = serializers.SerializerMethodField('get_file_url')
    filename = serializers.SerializerMethodField('get_file_filename')

    class Meta:
        model = CollectionCourtDecision
        fields = ('id', 'lease', 'file', 'filename', 'uploader', 'uploaded_at')
        download_url_name = 'collectioncourtdecision-download'


class CollectionLetterSerializer(FileSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    uploader = UserSerializer()
    file = serializers.SerializerMethodField('get_file_url')
    filename = serializers.SerializerMethodField('get_file_filename')

    class Meta:
        model = CollectionLetter
        fields = ('id', 'lease', 'file', 'filename', 'uploader', 'uploaded_at')
        download_url_name = 'collectionletter-download'


class CollectionLetterTemplateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = CollectionLetterTemplate
        fields = ('id', 'name')


class CollectionNoteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    user = UserSerializer(read_only=True)

    class Meta:
        model = CollectionNote
        fields = '__all__'


class CollectionNoteCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CollectionNote
        fields = ('id', 'note', 'user')
