from django.utils import timezone
from rest_framework import serializers

from customers.serializers import CustomerSerializer
from finance.models import InvoiceRequest
from orders.serializers import OrderListSerializer


def next_invoice_request_no():
    prefix = timezone.localdate().strftime("INV%Y%m%d")
    latest = InvoiceRequest.objects.filter(request_no__startswith=prefix).order_by("-request_no").first()
    next_index = 1
    if latest:
        try:
            next_index = int(latest.request_no[-3:]) + 1
        except ValueError:
            next_index = InvoiceRequest.objects.filter(request_no__startswith=prefix).count() + 1
    return f"{prefix}{next_index:03d}"


class InvoiceRequestSerializer(serializers.ModelSerializer):
    order_info = OrderListSerializer(source="order", read_only=True)
    customer_info = CustomerSerializer(source="customer", read_only=True)
    applicant_name = serializers.CharField(source="applicant.get_full_name", read_only=True)
    approver_name = serializers.CharField(source="approver.get_full_name", read_only=True)

    class Meta:
        model = InvoiceRequest
        fields = [
            "id",
            "request_no",
            "order",
            "order_info",
            "customer",
            "customer_info",
            "invoice_type",
            "amount",
            "title",
            "tax_number",
            "remark",
            "approval_remark",
            "status",
            "applicant",
            "applicant_name",
            "approver",
            "approver_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "request_no",
            "status",
            "applicant",
            "applicant_name",
            "approver",
            "approver_name",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"customer": {"required": False}}

    def validate(self, attrs):
        order = attrs.get("order")
        customer = attrs.get("customer")
        if order and not customer:
            attrs["customer"] = order.customer
        if order and customer and order.customer_id != customer.id:
            raise serializers.ValidationError("发票申请的客户必须与订单客户一致。")
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["request_no"] = next_invoice_request_no()
        validated_data["applicant"] = request.user
        validated_data["created_by"] = request.user
        return super().create(validated_data)
