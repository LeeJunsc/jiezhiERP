from datetime import timedelta
from decimal import Decimal

from django.db.models import Exists, OuterRef, Sum
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


ALL_KANBAN_METRICS = [
    "amount",
    "order_count",
    "returning_customer_order_count",
    "after_sales_order_count",
    "pending_design_order_count",
    "pending_production_order_count",
    "pending_invoice_count",
]


def user_role_names(user):
    if user.is_superuser:
        return {"管理员"}
    return set(user.groups.values_list("name", flat=True))


def visible_kanban_metrics(user):
    roles = user_role_names(user)
    if "管理员" in roles or "财务" in roles:
        return ALL_KANBAN_METRICS

    visible = []
    role_metrics = {
        "销售": [
            "amount",
            "order_count",
            "returning_customer_order_count",
            "pending_design_order_count",
            "pending_production_order_count",
            "pending_invoice_count",
            "after_sales_order_count",
        ],
        "设计": ["pending_design_order_count", "after_sales_order_count"],
        "生产": ["pending_production_order_count", "after_sales_order_count"],
        "售后": ["order_count", "after_sales_order_count"],
    }
    for role in roles:
        for metric in role_metrics.get(role, []):
            if metric not in visible:
                visible.append(metric)
    return visible or ["order_count"]


def scoped_order_queryset(user):
    roles = user_role_names(user)
    queryset = Order.objects.all()
    if "销售" in roles and "管理员" not in roles and "财务" not in roles:
        return queryset.filter(salesperson=user)
    return queryset


def scoped_after_sales_queryset(user):
    roles = user_role_names(user)
    queryset = AfterSalesRequest.objects.all()
    if "销售" in roles and "管理员" not in roles and "财务" not in roles:
        return queryset.filter(order__salesperson=user)
    return queryset


def scoped_invoice_queryset(user):
    roles = user_role_names(user)
    queryset = InvoiceRequest.objects.all()
    if "销售" in roles and "管理员" not in roles and "财务" not in roles:
        return queryset.filter(order__salesperson=user)
    return queryset


def returning_order_count(orders, history_orders):
    previous_orders = history_orders.filter(customer=OuterRef("customer"), created_at__lt=OuterRef("created_at"))
    return orders.annotate(has_previous_order=Exists(previous_orders)).filter(has_previous_order=True).count()


def pick_metrics(values, visible_metrics):
    return {key: values[key] for key in visible_metrics}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    today = timezone.localdate()
    orders = scoped_order_queryset(request.user)
    after_sales = scoped_after_sales_queryset(request.user)
    invoices = scoped_invoice_queryset(request.user)
    today_orders = orders.filter(created_at__date=today)
    recent_orders = (
        orders.select_related("store", "customer", "salesperson", "design_option")
        .order_by("-created_at")[:5]
    )
    return Response(
        {
            "orders": orders.count(),
            "pending_design": orders.filter(status__in=[Order.Status.PENDING_DESIGN, Order.Status.DESIGNING]).count(),
            "pending_production": orders.filter(status=Order.Status.PENDING_PRODUCTION).count(),
            "completed": orders.filter(status=Order.Status.COMPLETED).count(),
            "today_order_amount": money(today_orders.aggregate(total=Sum("total_amount"))["total"]),
            "today_order_count": today_orders.count(),
            "pending_after_sales": after_sales.filter(
                status__in=[AfterSalesRequest.Status.PENDING, AfterSalesRequest.Status.PROCESSING]
            ).count(),
            "pending_invoices": invoices.filter(status=InvoiceRequest.Status.PENDING).count(),
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

    visible_metrics = visible_kanban_metrics(request.user)
    orders = scoped_order_queryset(request.user)
    after_sales = scoped_after_sales_queryset(request.user)
    invoices = scoped_invoice_queryset(request.user)

    days = []
    current = start_date
    while current <= end_date:
        day_orders = orders.filter(created_at__date=current)
        amount = day_orders.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        returning_count = returning_order_count(day_orders, orders)
        after_sales_order_count = (
            after_sales.filter(created_at__date=current).values("order_id").distinct().count()
        )
        pending_design_order_count = day_orders.filter(status__in=[Order.Status.PENDING_DESIGN, Order.Status.DESIGNING]).count()
        pending_production_order_count = day_orders.filter(status=Order.Status.PENDING_PRODUCTION).count()
        pending_invoice_count = invoices.filter(created_at__date=current, status=InvoiceRequest.Status.PENDING).count()
        day_values = {
            "amount": money(amount),
            "order_count": day_orders.count(),
            "returning_customer_order_count": returning_count,
            "after_sales_order_count": after_sales_order_count,
            "pending_design_order_count": pending_design_order_count,
            "pending_production_order_count": pending_production_order_count,
            "pending_invoice_count": pending_invoice_count,
        }
        days.append(
            {
                "date": current.isoformat(),
                **pick_metrics(day_values, visible_metrics),
            }
        )
        current += timedelta(days=1)

    period_orders = orders.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
    period_after_sales = after_sales.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
    period_pending_invoices = invoices.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        status=InvoiceRequest.Status.PENDING,
    )
    returning_total = returning_order_count(period_orders, orders)
    summary_values = {
        "amount": money(period_orders.aggregate(total=Sum("total_amount"))["total"]),
        "order_count": period_orders.count(),
        "returning_customer_order_count": returning_total,
        "after_sales_order_count": period_after_sales.values("order_id").distinct().count(),
        "pending_design_order_count": period_orders.filter(status__in=[Order.Status.PENDING_DESIGN, Order.Status.DESIGNING]).count(),
        "pending_production_order_count": period_orders.filter(status=Order.Status.PENDING_PRODUCTION).count(),
        "pending_invoice_count": period_pending_invoices.count(),
    }

    return Response(
        {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "visible_metrics": visible_metrics,
            "summary": pick_metrics(summary_values, visible_metrics),
            "series": days,
        }
    )
