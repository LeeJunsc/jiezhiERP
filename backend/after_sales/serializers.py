from django.utils import timezone
from rest_framework import serializers

from after_sales.models import AfterSalesRequest
from orders.serializers import OrderListSerializer


def next_after_sales_request_no():
    prefix = timezone.localdate().strftime("AS%Y%m%d")
    latest = AfterSalesRequest.objects.filter(request_no__startswith=prefix).order_by("-request_no").first()
    next_index = 1
    if latest:
        try:
            next_index = int(latest.request_no[-3:]) + 1
        except ValueError:
            next_index = AfterSalesRequest.objects.filter(request_no__startswith=prefix).count() + 1
    return f"{prefix}{next_index:03d}"


class AfterSalesRequestSerializer(serializers.ModelSerializer):
    order_info = OrderListSerializer(source="order", read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)

    class Meta:
        model = AfterSalesRequest
        fields = [
            "id",
            "request_no",
            "order",
            "order_info",
            "type",
            "status",
            "description",
            "solution",
            "remark",
            "refund_amount",
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "request_no", "status", "owner", "owner_name", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["request_no"] = next_after_sales_request_no()
        validated_data["created_by"] = request.user
        return super().create(validated_data)
