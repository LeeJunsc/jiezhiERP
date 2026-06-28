from django.db import models

from common.models import TimeStampedModel


class Customer(TimeStampedModel):
    name = models.CharField(max_length=120)
    source = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    company = models.CharField(max_length=160, blank=True)
    wechat = models.CharField(max_length=80, blank=True)
    whatsapp = models.CharField(max_length=80, blank=True)
    line = models.CharField(max_length=80, blank=True)
    tags = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    invoice_title = models.CharField(max_length=200, blank=True)
    tax_number = models.CharField(max_length=80, blank=True)
    remark = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["source"]),
        ]

    def __str__(self):
        return self.name
