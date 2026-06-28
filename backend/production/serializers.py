from rest_framework import serializers

from orders.serializers import OrderListSerializer
from production.models import ProductionArrangement


class ProductionArrangementSerializer(serializers.ModelSerializer):
    order = OrderListSerializer(read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)

    class Meta:
        model = ProductionArrangement
        fields = [
            "id",
            "arrangement_no",
            "order",
            "owner",
            "owner_name",
            "factory_name",
            "status",
            "planned_finish_at",
            "confirmed_at",
            "remark",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "arrangement_no", "confirmed_at", "created_at", "updated_at"]
