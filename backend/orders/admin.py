from django.contrib import admin

from orders.models import DesignOption, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(DesignOption)
class DesignOptionAdmin(admin.ModelAdmin):
    list_display = ["name", "requires_design", "sort_order", "status"]
    list_filter = ["requires_design", "status"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_no", "store", "customer", "status", "total_amount", "payment_channel", "delivery_date", "created_at"]
    list_filter = ["status", "store", "design_option", "payment_channel"]
    search_fields = ["order_no", "platform_order_no", "customer__name", "customer__phone"]
    inlines = [OrderItemInline]
