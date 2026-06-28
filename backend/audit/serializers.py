from rest_framework import serializers

from audit.models import OperationLog


class OperationLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.get_full_name", read_only=True)

    class Meta:
        model = OperationLog
        fields = ["id", "actor", "actor_name", "business_type", "business_id", "action", "before_value", "after_value", "remark", "created_at"]
