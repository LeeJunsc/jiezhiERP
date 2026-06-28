from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class ProductionArrangement(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "待安排"
        SCHEDULED = "scheduled", "已安排"
        CONFIRMED = "confirmed", "已确认"
        EXCEPTION = "exception", "异常"

    arrangement_no = models.CharField(max_length=40, unique=True)
    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="production_arrangement")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    factory_name = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    planned_finish_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    remark = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["planned_finish_at"]),
        ]

    def __str__(self):
        return self.arrangement_no
