from rest_framework import serializers

from system_settings.models import PaymentChannel


class PaymentChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentChannel
        fields = ["id", "name", "code", "is_default", "sort_order", "status", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
