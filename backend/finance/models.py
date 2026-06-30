from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class InvoiceRequest(TimeStampedModel):
    class InvoiceType(models.TextChoices):
        NORMAL = "normal", "普通13%"
        SPECIAL = "special", "专票13%"

    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        PENDING = "pending", "待审批"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已驳回"
        WITHDRAWN = "withdrawn", "已撤回"

    request_no = models.CharField(max_length=40, unique=True)
    order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.SET_NULL, related_name="invoice_requests")
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="invoice_requests")
    invoice_type = models.CharField(max_length=30, choices=InvoiceType.choices, default=InvoiceType.NORMAL)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    title = models.CharField(max_length=200)
    tax_number = models.CharField(max_length=80, blank=True)
    remark = models.TextField(blank=True)
    approval_remark = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="invoice_applications")
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="invoice_approvals")

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["order"]),
            models.Index(fields=["applicant"]),
        ]

    def __str__(self):
        return self.request_no
