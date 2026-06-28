from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class DesignTask(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "待领取"
        DESIGNING = "designing", "设计中"
        WAITING_CONFIRMATION = "waiting_confirmation", "待确认"
        NEEDS_CHANGES = "needs_changes", "需修改"
        CONFIRMED = "confirmed", "已确认"

    task_no = models.CharField(max_length=40, unique=True)
    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="design_task")
    designer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    due_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    remark = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["designer", "status"]),
            models.Index(fields=["due_at"]),
        ]

    def __str__(self):
        return self.task_no
