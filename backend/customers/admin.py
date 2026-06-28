from django.contrib import admin

from customers.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "source", "company", "phone", "wechat", "tags", "created_at"]
    list_filter = ["source"]
    search_fields = ["name", "company", "phone", "wechat", "whatsapp", "line", "tags"]
