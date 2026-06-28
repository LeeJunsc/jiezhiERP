from rest_framework import serializers

from customers.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "source",
            "phone",
            "company",
            "wechat",
            "whatsapp",
            "line",
            "tags",
            "address",
            "invoice_title",
            "tax_number",
            "remark",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
