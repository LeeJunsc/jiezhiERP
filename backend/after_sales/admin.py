from django.contrib import admin

from after_sales.models import AfterSalesRequest


@admin.register(AfterSalesRequest)
class AfterSalesRequestAdmin(admin.ModelAdmin):
    list_display = ["request_no", "order", "type", "status", "owner", "created_at"]
    list_filter = ["type", "status"]
    search_fields = ["request_no", "order__order_no", "description"]
