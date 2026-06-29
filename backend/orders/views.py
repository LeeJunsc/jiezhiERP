from django.db.models import Prefetch, Q, Sum
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from after_sales.models import AfterSalesRequest
from after_sales.serializers import AfterSalesRequestSerializer
from attachments.models import Attachment
from attachments.serializers import AttachmentSerializer
from audit.models import OperationLog
from audit.serializers import OperationLogSerializer
from common.permissions import IsAdminRole, IsSalesOrAdmin
from design.serializers import DesignTaskSerializer
from finance.models import InvoiceRequest
from finance.serializers import InvoiceRequestSerializer
from orders.models import DesignOption, Order
from orders.serializers import DesignOptionSerializer, OrderListSerializer, OrderSerializer
from orders.services import cancel_order, submit_order
from production.serializers import ProductionArrangementSerializer


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
            Order.objects.select_related(
                "store",
                "customer",
                "salesperson",
                "design_option",
                "payment_channel",
                "design_task",
                "production_arrangement",
            )
            .prefetch_related(
                "items",
                Prefetch(
                    "invoice_requests",
                    queryset=InvoiceRequest.objects.order_by("created_at"),
                    to_attr="prefetched_invoice_requests",
                ),
            )
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
                | Q(store__custom_platform__icontains=keyword)
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

    @action(detail=True, methods=["get"])
    def related(self, request, pk=None):
        order = self.get_object()
        context = {"request": request}

        try:
            design_task = order.design_task
        except ObjectDoesNotExist:
            design_task = None

        try:
            production_arrangement = order.production_arrangement
        except ObjectDoesNotExist:
            production_arrangement = None

        invoices = InvoiceRequest.objects.filter(order=order).select_related("customer", "applicant", "approver").order_by("-created_at")
        after_sales = AfterSalesRequest.objects.filter(order=order).select_related("order", "order__store", "order__customer", "owner").order_by("-created_at")

        attachment_targets = [("order", order.id)]
        if design_task:
            attachment_targets.append(("design", design_task.id))
        if production_arrangement:
            attachment_targets.append(("production", production_arrangement.id))
        attachment_targets.extend(("invoice", invoice.id) for invoice in invoices)
        attachment_targets.extend(("after_sales", item.id) for item in after_sales)

        attachments_by_key = {}
        for business_type, business_id in attachment_targets:
            attachments_by_key[f"{business_type}:{business_id}"] = []
        attachment_filter = Q()
        for business_type, business_id in attachment_targets:
            attachment_filter |= Q(business_type=business_type, business_id=business_id)
        if attachment_filter:
            attachments = Attachment.objects.filter(attachment_filter).order_by("-created_at")
            for attachment in attachments:
                key = f"{attachment.business_type}:{attachment.business_id}"
                attachments_by_key.setdefault(key, []).append(AttachmentSerializer(attachment, context=context).data)

        return Response(
            {
                "order_attachments": attachments_by_key.get(f"order:{order.id}", []),
                "design_task": DesignTaskSerializer(design_task, context=context).data if design_task else None,
                "design_attachments": attachments_by_key.get(f"design:{design_task.id}", []) if design_task else [],
                "production_arrangement": ProductionArrangementSerializer(production_arrangement, context=context).data if production_arrangement else None,
                "production_attachments": attachments_by_key.get(f"production:{production_arrangement.id}", []) if production_arrangement else [],
                "invoice_requests": [
                    {
                        **InvoiceRequestSerializer(invoice, context=context).data,
                        "attachments": attachments_by_key.get(f"invoice:{invoice.id}", []),
                    }
                    for invoice in invoices
                ],
                "after_sales_requests": [
                    {
                        **AfterSalesRequestSerializer(item, context=context).data,
                        "attachments": attachments_by_key.get(f"after_sales:{item.id}", []),
                    }
                    for item in after_sales
                ],
            }
        )

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
