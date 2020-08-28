from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.models import (
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchType,
)
from leasing.serializers.utils import NameModelSerializer
from users.models import User
from users.serializers import UserSerializer

from .utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin


class PlotSearchTypeSerializer(NameModelSerializer):
    class Meta:
        model = PlotSearchType
        fields = "__all__"


class PlotSearchSubtypeSerializer(NameModelSerializer):
    class Meta:
        model = PlotSearchSubtype
        fields = "__all__"


class PlotSearchStageSerializer(NameModelSerializer):
    class Meta:
        model = PlotSearchStage
        fields = "__all__"


class PlotSearchListSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    type = PlotSearchTypeSerializer()
    subtype = PlotSearchSubtypeSerializer()
    stage = PlotSearchStageSerializer()

    class Meta:
        model = PlotSearch
        fields = "__all__"


class PlotSearchRetrieveSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    type = PlotSearchTypeSerializer()
    subtype = PlotSearchSubtypeSerializer()
    stage = PlotSearchStageSerializer()
    preparer = UserSerializer()

    class Meta:
        model = PlotSearch
        fields = "__all__"


class PlotSearchUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    preparer = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=User.objects.all(),
        related_serializer=UserSerializer,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = PlotSearch
        fields = "__all__"


class PlotSearchCreateSerializer(PlotSearchUpdateSerializer):
    class Meta:
        model = PlotSearch
        fields = "__all__"
