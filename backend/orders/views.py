from django.db.models import Q, Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from audit.models import OperationLog
from audit.serializers import OperationLogSerializer
from common.permissions import IsAdminRole, IsSalesOrAdmin
from orders.models import DesignOption, Order
from orders.serializers import DesignOptionSerializer, OrderListSerializer, OrderSerializer
from orders.services import cancel_order, submit_order


class DesignOptionViewSet(viewsets.ModelViewSet):
    serializer_class = DesignOptionSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        queryset = DesignOption.objects.order_by("sort_order", "name")
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        option = self.get_object()
        option.status = DesignOption.Status.DISABLED
        option.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(option).data)


class OrderViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdminRole()]
        if self.action in ["create", "update", "partial_update", "submit", "cancel"]:
            return [IsSalesOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = (
            Order.objects.select_related("store", "customer", "salesperson", "design_option", "payment_channel")
            .prefetch_related("items")
            .order_by("-created_at")
        )
        params = self.request.query_params
        keyword = params.get("keyword")
        if keyword:
            queryset = queryset.filter(
                Q(order_no__icontains=keyword)
                | Q(platform_order_no__icontains=keyword)
                | Q(customer__name__icontains=keyword)
                | Q(customer__phone__icontains=keyword)
                | Q(customer__company__icontains=keyword)
                | Q(customer__wechat__icontains=keyword)
                | Q(customer__whatsapp__icontains=keyword)
                | Q(customer__line__icontains=keyword)
                | Q(customer__tags__icontains=keyword)
                | Q(customer__address__icontains=keyword)
                | Q(store__name__icontains=keyword)
                | Q(store__platform__icontains=keyword)
                | Q(design_option__name__icontains=keyword)
                | Q(payment_status__icontains=keyword)
                | Q(payment_channel__name__icontains=keyword)
                | Q(status__icontains=keyword)
                | Q(customization_note__icontains=keyword)
                | Q(remark__icontains=keyword)
                | Q(items__product_name__icontains=keyword)
                | Q(items__sku__icontains=keyword)
                | Q(items__custom_size__icontains=keyword)
                | Q(items__custom_color__icontains=keyword)
                | Q(items__custom_note__icontains=keyword)
            )
            queryset = queryset.distinct()
        if params.get("store_id"):
            queryset = queryset.filter(store_id=params["store_id"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("salesperson_id"):
            queryset = queryset.filter(salesperson_id=params["salesperson_id"])
        if params.get("created_from"):
            queryset = queryset.filter(created_at__date__gte=params["created_from"])
        if params.get("created_to"):
            queryset = queryset.filter(created_at__date__lte=params["created_to"])
        if params.get("delivery_from"):
            queryset = queryset.filter(delivery_date__gte=params["delivery_from"])
        if params.get("delivery_to"):
            queryset = queryset.filter(delivery_date__lte=params["delivery_to"])
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        order = submit_order(self.get_object(), request.user)
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = cancel_order(self.get_object(), request.user)
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["get"])
    def logs(self, request, pk=None):
        order = self.get_object()
        logs = OperationLog.objects.filter(business_type="Order", business_id=order.id).order_by("-created_at")
        return Response(OperationLogSerializer(logs, many=True).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        summary = queryset.aggregate(total_amount=Sum("total_amount"))
        return Response(
            {
                "order_count": queryset.count(),
                "total_amount": str(summary["total_amount"] or "0.00"),
            }
        )
