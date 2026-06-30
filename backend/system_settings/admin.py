from django.contrib import admin

from system_settings.models import InvoiceTypeOption, PaymentChannel


@admin.register(PaymentChannel)
class PaymentChannelAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_default", "sort_order", "status"]
    list_filter = ["status", "is_default"]
    search_fields = ["name", "code"]


@admin.register(InvoiceTypeOption)
class InvoiceTypeOptionAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "tax_rate", "sort_order", "status"]
    list_filter = ["status"]
    search_fields = ["name", "code"]
