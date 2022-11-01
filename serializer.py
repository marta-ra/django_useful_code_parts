from typing import Any

from django.db import transaction
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from app.models.employee import Employee
from app.models.training import TrainingList
from app.serializers.manager import (
    ManagerSerializer,
    ManagerSerializerFull,
)
from app.serializers.employee import AdditionalInfoSerializer
from app.utils import has_permission_to_edit, get_manager_for_employee




class BaseSerializer(serializers.ModelSerializer[Employee]):
    employee_id = serializers.UUIDField(read_only=True)
    login = serializers.CharField(read_only=True)
    creator_id = serializers.UUIDField(read_only=True)
    created = serializers.DateTimeField(read_only=True)
    updated = serializers.DateTimeField(read_only=True)
    additional_info = AdditionalInfoSerializer()
    allow_edit = serializers.SerializerMethodField(
        method_name='allow_edit'
    )

    class Meta:
        model = Employee
        fields = [
            'employee_id',
            'login',
            'creator_id',
            'created',
            'updated',
            'manager',
            'additional_info',
            'allow_edit'
        ]
        read_only_fields = [
            'employee_id',
            'login',
            'creator_id',
            'created',
            'updated',
            'allow_edit'
        ]

    def allow_edit(
            self,
            obj: Employee
    ) -> bool:
        request = self.context.get('request')
        return has_permission_to_edit(request.user, obj)


    @staticmethod
    def get_manager(obj: Employee) -> ReturnDict:
        manager = get_manager_for_employee(obj.employee_id)
        serializer = ManagerSerializer(manager)
        return serializer.data['manager']

    @staticmethod
    def get_manager_full(obj: Employee) -> ReturnDict:
        manager = get_manager_for_employee(obj.employee_id)
        serializer = ManagerSerializerFull(manager)
        return serializer.data
        

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> Employee:
        validated_data.update(
            {
                'creator_id': self.context['request'].user.id,
            }
        )
        report = super().create(validated_data)
        (
            TrainingList.objects
            .filter(login__in=self.data['login'])
            .update(hired=True)
        )
        return report


class SerializerShort(BaseSerializer):
    manager = serializers.SerializerMethodField('get_manager', required=False)


class SerializerFull(BaseSerializer):
    manager = serializers.SerializerMethodField(
        'get_manager_full',
        required=False
    )
