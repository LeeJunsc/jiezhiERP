from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Attachment(TimeStampedModel):
    class BusinessType(models.TextChoices):
        ORDER = "order", "订单"
        DESIGN = "design", "设计"
        PRODUCTION = "production", "生产"
        INVOICE = "invoice", "发票"
        PAYMENT = "payment", "付款"
        AFTER_SALES = "after_sales", "售后"

    file = models.FileField(upload_to="attachments/%Y/%m/%d/")
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=120, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    business_type = models.CharField(max_length=40, choices=BusinessType.choices)
    business_id = models.UUIDField()
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_attachments")

    class Meta:
        indexes = [
            models.Index(fields=["business_type", "business_id"]),
            models.Index(fields=["uploader"]),
        ]

    def __str__(self):
        return self.file_name
