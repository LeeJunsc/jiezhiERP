from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from customers.serializers import CustomerSerializer
from orders.models import DesignOption, Order, OrderItem
from stores.serializers import StoreSerializer
from system_settings.serializers import PaymentChannelSerializer


class DesignOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignOption
        fields = ["id", "name", "requires_design", "sort_order", "status", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "sku",
            "quantity",
            "unit_price",
            "line_amount",
            "custom_size",
            "custom_color",
            "custom_note",
        ]
        read_only_fields = ["id"]


class OrderListSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)
    design_option = DesignOptionSerializer(read_only=True)
    payment_channel = PaymentChannelSerializer(read_only=True)
    salesperson_name = serializers.CharField(source="salesperson.get_full_name", read_only=True)
    design_finalized_at = serializers.SerializerMethodField()
    production_arranged_at = serializers.SerializerMethodField()
    invoice_requested_at = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_no",
            "platform_order_no",
            "store",
            "customer",
            "salesperson",
            "salesperson_name",
            "design_option",
            "status",
            "total_amount",
            "paid_amount",
            "payment_status",
            "payment_channel",
            "delivery_date",
            "urgent",
            "design_finalized_at",
            "production_arranged_at",
            "invoice_requested_at",
            "created_at",
            "updated_at",
        ]

    def get_design_finalized_at(self, obj):
        try:
            return obj.design_task.confirmed_at
        except ObjectDoesNotExist:
            return None

    def get_production_arranged_at(self, obj):
        try:
            return obj.production_arrangement.created_at
        except ObjectDoesNotExist:
            return None

    def get_invoice_requested_at(self, obj):
        invoices = getattr(obj, "prefetched_invoice_requests", None)
        if invoices is not None:
            return invoices[0].created_at if invoices else None
        invoice = obj.invoice_requests.order_by("created_at").first()
        return invoice.created_at if invoice else None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    order_no = serializers.CharField(required=False, allow_blank=True)
    store_info = StoreSerializer(source="store", read_only=True)
    customer_info = CustomerSerializer(source="customer", read_only=True)
    design_option_info = DesignOptionSerializer(source="design_option", read_only=True)
    payment_channel_info = PaymentChannelSerializer(source="payment_channel", read_only=True)
    salesperson_name = serializers.CharField(source="salesperson.get_full_name", read_only=True)
    design_finalized_at = serializers.SerializerMethodField()
    production_arranged_at = serializers.SerializerMethodField()
    invoice_requested_at = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_no",
            "platform_order_no",
            "store",
            "store_info",
            "customer",
            "customer_info",
            "salesperson",
            "salesperson_name",
            "design_option",
            "design_option_info",
            "status",
            "total_amount",
            "paid_amount",
            "payment_status",
            "payment_channel",
            "payment_channel_info",
            "delivery_date",
            "urgent",
            "customization_note",
            "remark",
            "submitted_at",
            "completed_at",
            "design_finalized_at",
            "production_arranged_at",
            "invoice_requested_at",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "submitted_at", "completed_at", "created_at", "updated_at"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance and self.instance.status == Order.Status.CANCELLED:
            return attrs

        errors = {}
        if not attrs.get("customer") and not getattr(self.instance, "customer_id", None):
            errors["customer"] = "请选择客户。"
        if not attrs.get("store") and not getattr(self.instance, "store_id", None):
            errors["store"] = "请选择来源店铺。"
        if not attrs.get("design_option") and not getattr(self.instance, "design_option_id", None):
            errors["design_option"] = "请选择设计处理方式。"
        if "total_amount" in attrs and attrs.get("total_amount") in [None, 0]:
            errors["total_amount"] = "请填写订单金额。"

        platform_order_no = (attrs.get("platform_order_no") or getattr(self.instance, "platform_order_no", "") or "").strip()
        if not platform_order_no:
            errors["platform_order_no"] = "请填写平台订单号。"

        if errors:
            raise serializers.ValidationError(errors)

        duplicate_queryset = (
            Order.objects.filter(platform_order_no=platform_order_no)
            .exclude(status=Order.Status.CANCELLED)
            .only("id", "order_no")
        )
        if self.instance:
            duplicate_queryset = duplicate_queryset.exclude(id=self.instance.id)

        duplicate = duplicate_queryset.first()
        if duplicate:
            raise serializers.ValidationError(
                {
                    "platform_order_no": f"平台订单号已存在，关联订单：{duplicate.order_no}。非撤销订单不允许重复提交。"
                }
            )

        attrs["platform_order_no"] = platform_order_no
        return attrs

    def get_design_finalized_at(self, obj):
        try:
            return obj.design_task.confirmed_at
        except ObjectDoesNotExist:
            return None

    def get_production_arranged_at(self, obj):
        try:
            return obj.production_arrangement.created_at
        except ObjectDoesNotExist:
            return None

    def get_invoice_requested_at(self, obj):
        invoices = getattr(obj, "prefetched_invoice_requests", None)
        if invoices is not None:
            return invoices[0].created_at if invoices else None
        invoice = obj.invoice_requests.order_by("created_at").first()
        return invoice.created_at if invoice else None

    def create(self, validated_data):
        from orders.services import next_order_no

        items_data = validated_data.pop("items", [])
        if not items_data:
            raise serializers.ValidationError({"items": "请至少填写一个产品。"})
        if not validated_data.get("order_no"):
            validated_data["order_no"] = next_order_no()
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            if not item_data.get("line_amount"):
                item_data["line_amount"] = item_data["quantity"] * item_data["unit_price"]
            OrderItem.objects.create(order=order, created_by=order.created_by, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                if not item_data.get("line_amount"):
                    item_data["line_amount"] = item_data["quantity"] * item_data["unit_price"]
                OrderItem.objects.create(order=instance, created_by=instance.created_by, **item_data)
        return instance
