from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class DesignOption(TimeStampedModel):
    class Status(models.TextChoices):
        ENABLED = "enabled", "启用"
        DISABLED = "disabled", "停用"

    name = models.CharField(max_length=120)
    requires_design = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENABLED)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [models.Index(fields=["status", "sort_order"])]

    def __str__(self):
        return self.name


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        SUBMITTED = "submitted", "已提交"
        PENDING_DESIGN = "pending_design", "待设计"
        DESIGNING = "designing", "设计中"
        DESIGN_CONFIRMED = "design_confirmed", "设计确认"
        PENDING_PRODUCTION = "pending_production", "待生产安排"
        COMPLETED = "completed", "已完成"
        CANCELLED = "cancelled", "已取消"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "未收款"
        PARTIAL = "partial", "部分收款"
        PAID = "paid", "已收款"

    order_no = models.CharField(max_length=40, unique=True)
    platform_order_no = models.CharField(max_length=80, blank=True)
    store = models.ForeignKey("stores.Store", on_delete=models.PROTECT, related_name="orders")
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="orders")
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sales_orders")
    design_option = models.ForeignKey(DesignOption, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=30, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    payment_channel = models.ForeignKey(
        "system_settings.PaymentChannel",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    delivery_date = models.DateField(null=True, blank=True)
    urgent = models.BooleanField(default=False)
    customization_note = models.TextField(blank=True)
    remark = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["order_no"]),
            models.Index(fields=["platform_order_no"]),
            models.Index(fields=["store", "status"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["salesperson"]),
            models.Index(fields=["design_option"]),
            models.Index(fields=["payment_channel"]),
            models.Index(fields=["delivery_date"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return self.order_no


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=120, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    custom_size = models.CharField(max_length=120, blank=True)
    custom_color = models.CharField(max_length=120, blank=True)
    custom_note = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["order"])]

    def __str__(self):
        return f"{self.order.order_no} - {self.product_name}"
