from django.db import models

from common.models import TimeStampedModel


class PaymentChannel(TimeStampedModel):
    class Status(models.TextChoices):
        ENABLED = "enabled", "启用"
        DISABLED = "disabled", "停用"

    name = models.CharField(max_length=80)
    code = models.SlugField(max_length=60, unique=True)
    is_default = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENABLED)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["status", "sort_order"]),
            models.Index(fields=["is_default"]),
        ]

    def __str__(self):
        return self.name
