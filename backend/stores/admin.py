from django.contrib import admin

from stores.models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ["name", "platform", "status", "owner", "created_at"]
    list_filter = ["platform", "status"]
    search_fields = ["name"]
