from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Store(TimeStampedModel):
    class Platform(models.TextChoices):
        TAOBAO = "taobao", "淘宝"
        PINDUODUO = "pinduoduo", "拼多多"
        DOUYIN = "douyin", "抖音"
        XIAOHONGSHU = "xiaohongshu", "小红书"
        OTHER = "other", "其他"

    class Status(models.TextChoices):
        ENABLED = "enabled", "启用"
        DISABLED = "disabled", "停用"

    name = models.CharField(max_length=120)
    platform = models.CharField(max_length=40, choices=Platform.choices)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENABLED)

    class Meta:
        indexes = [
            models.Index(fields=["platform"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.name
