from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from after_sales.models import AfterSalesRequest
from finance.models import InvoiceRequest
from orders.models import Order
from orders.serializers import OrderListSerializer


def money(value):
    return str(value or Decimal("0.00"))


def parse_date(value, default):
    if not value:
        return default
    try:
        return timezone.datetime.fromisoformat(value).date()
    except ValueError:
        return default


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    today = timezone.localdate()
    today_orders = Order.objects.filter(created_at__date=today)
    recent_orders = (
        Order.objects.select_related("store", "customer", "salesperson", "design_option")
        .order_by("-created_at")[:5]
    )
    return Response(
        {
            "orders": Order.objects.count(),
            "pending_design": Order.objects.filter(status__in=[Order.Status.PENDING_DESIGN, Order.Status.DESIGNING]).count(),
            "pending_production": Order.objects.filter(status=Order.Status.PENDING_PRODUCTION).count(),
            "completed": Order.objects.filter(status=Order.Status.COMPLETED).count(),
            "today_order_amount": money(today_orders.aggregate(total=Sum("total_amount"))["total"]),
            "today_order_count": today_orders.count(),
            "pending_after_sales": AfterSalesRequest.objects.filter(
                status__in=[AfterSalesRequest.Status.PENDING, AfterSalesRequest.Status.PROCESSING]
            ).count(),
            "pending_invoices": InvoiceRequest.objects.filter(status=InvoiceRequest.Status.PENDING).count(),
            "recent_orders": OrderListSerializer(recent_orders, many=True).data,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_kanban(request):
    today = timezone.localdate()
    start_date = parse_date(request.query_params.get("start_date"), today - timedelta(days=6))
    end_date = parse_date(request.query_params.get("end_date"), today)
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    days = []
    current = start_date
    while current <= end_date:
        day_orders = Order.objects.filter(created_at__date=current)
        amount = day_orders.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        returning_count = 0
        for order in day_orders.select_related("customer"):
            if Order.objects.filter(customer=order.customer, created_at__lt=order.created_at).exists():
                returning_count += 1
        after_sales_order_count = (
            AfterSalesRequest.objects.filter(created_at__date=current).values("order_id").distinct().count()
        )
        days.append(
            {
                "date": current.isoformat(),
                "amount": money(amount),
                "order_count": day_orders.count(),
                "returning_customer_order_count": returning_count,
                "after_sales_order_count": after_sales_order_count,
            }
        )
        current += timedelta(days=1)

    period_orders = Order.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
    period_after_sales = AfterSalesRequest.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
    returning_total = 0
    for order in period_orders.select_related("customer"):
        if Order.objects.filter(customer=order.customer, created_at__lt=order.created_at).exists():
            returning_total += 1

    return Response(
        {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "summary": {
                "amount": money(period_orders.aggregate(total=Sum("total_amount"))["total"]),
                "order_count": period_orders.count(),
                "returning_customer_order_count": returning_total,
                "after_sales_order_count": period_after_sales.values("order_id").distinct().count(),
            },
            "series": days,
        }
    )
