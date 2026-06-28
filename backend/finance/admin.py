from django.contrib import admin

from finance.models import InvoiceRequest


@admin.register(InvoiceRequest)
class InvoiceRequestAdmin(admin.ModelAdmin):
    list_display = ["request_no", "customer", "amount", "invoice_type", "status", "applicant", "created_at"]
    list_filter = ["status", "invoice_type"]
    search_fields = ["request_no", "customer__name", "title"]
