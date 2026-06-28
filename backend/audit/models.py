from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class OperationLog(TimeStampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="operation_logs")
    business_type = models.CharField(max_length=40)
    business_id = models.UUIDField()
    action = models.CharField(max_length=80)
    before_value = models.JSONField(null=True, blank=True)
    after_value = models.JSONField(null=True, blank=True)
    remark = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["business_type", "business_id"]),
            models.Index(fields=["actor"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.business_type}:{self.action}"
