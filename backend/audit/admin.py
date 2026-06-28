from django.contrib import admin

from audit.models import OperationLog


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ["business_type", "business_id", "action", "actor", "created_at"]
    list_filter = ["business_type", "action"]
    search_fields = ["action", "remark"]
