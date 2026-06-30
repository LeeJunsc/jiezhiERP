from django.db.models import Q, Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import IsFinanceOrAdmin
from finance.models import InvoiceRequest
from finance.serializers import InvoiceRequestSerializer


class InvoiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceRequestSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ["approve", "reject", "destroy"]:
            return [IsFinanceOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = (
            InvoiceRequest.objects.select_related("order", "order__store", "order__customer", "customer", "applicant", "approver")
            .order_by("-created_at")
        )
        params = self.request.query_params
        keyword = params.get("keyword")
        if keyword:
            queryset = queryset.filter(
                Q(request_no__icontains=keyword)
                | Q(order__order_no__icontains=keyword)
                | Q(order__platform_order_no__icontains=keyword)
                | Q(customer__name__icontains=keyword)
                | Q(customer__phone__icontains=keyword)
                | Q(title__icontains=keyword)
                | Q(tax_number__icontains=keyword)
                | Q(remark__icontains=keyword)
            )
        if params.get("status"):
            statuses = [status for status in params["status"].split(",") if status]
            queryset = queryset.filter(status__in=statuses)
        if params.get("created_from"):
            queryset = queryset.filter(created_at__date__gte=params["created_from"])
        if params.get("created_to"):
            queryset = queryset.filter(created_at__date__lte=params["created_to"])
        return queryset

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        invoice = self.get_object()
        invoice.status = InvoiceRequest.Status.APPROVED
        invoice.approver = request.user
        invoice.approval_remark = request.data.get("approval_remark", invoice.approval_remark)
        invoice.save(update_fields=["status", "approver", "approval_remark", "updated_at"])
        return Response(self.get_serializer(invoice).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        invoice = self.get_object()
        invoice.status = InvoiceRequest.Status.REJECTED
        invoice.approver = request.user
        invoice.approval_remark = request.data.get("approval_remark", invoice.approval_remark)
        invoice.save(update_fields=["status", "approver", "approval_remark", "updated_at"])
        return Response(self.get_serializer(invoice).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        summary = queryset.aggregate(total_amount=Sum("amount"))
        return Response(
            {
                "request_count": queryset.count(),
                "total_amount": str(summary["total_amount"] or "0.00"),
            }
        )
