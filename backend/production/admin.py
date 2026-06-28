from django.contrib import admin

from production.models import ProductionArrangement


@admin.register(ProductionArrangement)
class ProductionArrangementAdmin(admin.ModelAdmin):
    list_display = ["arrangement_no", "order", "owner", "factory_name", "status", "planned_finish_at", "confirmed_at"]
    list_filter = ["status", "factory_name"]
    search_fields = ["arrangement_no", "order__order_no", "factory_name"]
