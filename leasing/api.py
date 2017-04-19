from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers, viewsets

from .models import Application, BuildingFootprint


class BuildingFootprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildingFootprint
        fields = ('use', 'area')


class ApplicationSerializer(EnumSupportSerializerMixin, serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    building_footprints = BuildingFootprintSerializer(many=True)

    class Meta:
        model = Application
        fields = '__all__'

    def create(self, validated_data):
        building_footprints = validated_data.pop('building_footprints')

        instance = super().create(validated_data)

        for building_footprint in building_footprints:
            BuildingFootprint.objects.create(
                application=instance,
                use=building_footprint['use'],
                area=building_footprint['area']
            )

        return instance

    def update(self, instance, validated_data):
        building_footprints = validated_data.pop('building_footprints')

        instance.building_footprints.all().delete()

        for building_footprint in building_footprints:
            BuildingFootprint.objects.create(
                application=instance,
                use=building_footprint['use'],
                area=building_footprint['area']
            )

        instance = super().update(instance, validated_data)

        return instance


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
