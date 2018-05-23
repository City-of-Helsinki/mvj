from rest_framework import serializers

from leasing.models import ContractRent, FixedInitialYearRent, Index, Rent, RentAdjustment
from leasing.serializers.rent import (
    ContractRentSerializer, FixedInitialYearRentSerializer, IndexSerializer, RentAdjustmentSerializer,
    RentSimpleSerializer)


class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)

        return serializer.data


class SubjectSerializer(serializers.Serializer):
    def to_representation(self, instance):
        serializer_map = {
            ContractRent: ContractRentSerializer,
            RentAdjustment: RentAdjustmentSerializer,
            Rent: RentSimpleSerializer,
            FixedInitialYearRent: FixedInitialYearRentSerializer,
            Index: IndexSerializer,
        }

        for model_class, serializer_class in serializer_map.items():
            if isinstance(instance, model_class):
                s = serializer_class()
                data = s.to_representation(instance)
                data['subject_type'] = model_class._meta.model_name

                return data

        return instance


class DateRangeField(serializers.Field):
    def to_internal_value(self, data):
        pass

    def to_representation(self, instance):
        return {
            'start_date': instance[0],
            'end_date': instance[1],
        }


class ExplanationItemSerializer(serializers.Serializer):
    subject = SubjectSerializer(read_only=True)
    sub_items = RecursiveSerializer(many=True, read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    date_ranges = serializers.ListField(child=DateRangeField(read_only=True))


class ExplanationSerializer(serializers.Serializer):
    items = serializers.ListField(child=ExplanationItemSerializer(read_only=True))
