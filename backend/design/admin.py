from django.contrib import admin

from design.models import DesignTask


@admin.register(DesignTask)
class DesignTaskAdmin(admin.ModelAdmin):
    list_display = ["task_no", "order", "designer", "status", "due_at", "confirmed_at"]
    list_filter = ["status"]
    search_fields = ["task_no", "order__order_no"]
