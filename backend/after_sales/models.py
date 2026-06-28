from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class AfterSalesRequest(TimeStampedModel):
    class Type(models.TextChoices):
        REFUND = "refund", "退款"
        RESHIP = "reship", "补发"
        REPAIR = "repair", "返修"
        COMPLAINT = "complaint", "投诉"
        OTHER = "other", "其他"

    class Status(models.TextChoices):
        PENDING = "pending", "待受理"
        PROCESSING = "processing", "处理中"
        COMPLETED = "completed", "已完成"
        CLOSED = "closed", "已关闭"

    request_no = models.CharField(max_length=40, unique=True)
    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="after_sales_requests")
    type = models.CharField(max_length=30, choices=Type.choices)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    description = models.TextField()
    solution = models.TextField(blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="after_sales_cases")

    class Meta:
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["status"]),
            models.Index(fields=["owner", "status"]),
        ]

    def __str__(self):
        return self.request_no
