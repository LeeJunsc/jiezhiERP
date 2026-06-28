from rest_framework import serializers

from design.models import DesignTask
from orders.serializers import OrderListSerializer


class DesignTaskSerializer(serializers.ModelSerializer):
    order = OrderListSerializer(read_only=True)
    designer_name = serializers.CharField(source="designer.get_full_name", read_only=True)

    class Meta:
        model = DesignTask
        fields = ["id", "task_no", "order", "designer", "designer_name", "status", "due_at", "confirmed_at", "remark", "created_at", "updated_at"]
        read_only_fields = ["id", "task_no", "confirmed_at", "created_at", "updated_at"]
