from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from after_sales.models import AfterSalesRequest
from after_sales.serializers import AfterSalesRequestSerializer
from common.permissions import IsAfterSalesOrAdmin


class AfterSalesRequestViewSet(viewsets.ModelViewSet):
    serializer_class = AfterSalesRequestSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ["start", "complete", "close", "reject", "destroy"]:
            return [IsAfterSalesOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = (
            AfterSalesRequest.objects.select_related("order", "order__store", "order__customer", "owner")
            .order_by("-created_at")
        )
        params = self.request.query_params
        keyword = params.get("keyword")
        if keyword:
            queryset = queryset.filter(
                Q(request_no__icontains=keyword)
                | Q(order__order_no__icontains=keyword)
                | Q(order__platform_order_no__icontains=keyword)
                | Q(order__customer__name__icontains=keyword)
                | Q(order__customer__phone__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(solution__icontains=keyword)
                | Q(remark__icontains=keyword)
            )
        if params.get("status"):
            statuses = [status for status in params["status"].split(",") if status]
            queryset = queryset.filter(status__in=statuses)
        if params.get("type"):
            queryset = queryset.filter(type=params["type"])
        if params.get("created_from"):
            queryset = queryset.filter(created_at__date__gte=params["created_from"])
        if params.get("created_to"):
            queryset = queryset.filter(created_at__date__lte=params["created_to"])
        return queryset

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        after_sales = self.get_object()
        after_sales.status = AfterSalesRequest.Status.PROCESSING
        after_sales.owner = request.user
        after_sales.solution = request.data.get("solution", after_sales.solution)
        after_sales.remark = request.data.get("remark", after_sales.remark)
        after_sales.save(update_fields=["status", "owner", "solution", "remark", "updated_at"])
        return Response(self.get_serializer(after_sales).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        after_sales = self.get_object()
        after_sales.status = AfterSalesRequest.Status.COMPLETED
        after_sales.owner = request.user
        after_sales.solution = request.data.get("solution", after_sales.solution)
        after_sales.remark = request.data.get("remark", after_sales.remark)
        after_sales.save(update_fields=["status", "owner", "solution", "remark", "updated_at"])
        return Response(self.get_serializer(after_sales).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        return self.reject(request, pk)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        after_sales = self.get_object()
        after_sales.status = AfterSalesRequest.Status.CLOSED
        after_sales.owner = request.user
        after_sales.solution = request.data.get("solution", after_sales.solution)
        after_sales.remark = request.data.get("remark", after_sales.remark)
        after_sales.save(update_fields=["status", "owner", "solution", "remark", "updated_at"])
        return Response(self.get_serializer(after_sales).data)
