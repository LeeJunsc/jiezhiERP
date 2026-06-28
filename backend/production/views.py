from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import IsProductionOrAdmin
from production.models import ProductionArrangement
from production.serializers import ProductionArrangementSerializer
from production.services import confirm_arrangement, schedule_arrangement


class ProductionArrangementViewSet(viewsets.ModelViewSet):
    serializer_class = ProductionArrangementSerializer
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ["schedule", "confirm", "mark_exception", "partial_update"]:
            return [IsProductionOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = ProductionArrangement.objects.select_related(
            "order",
            "order__store",
            "order__customer",
            "order__design_option",
            "owner",
        ).order_by("-created_at")
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset

    @action(detail=True, methods=["post"])
    def schedule(self, request, pk=None):
        arrangement = schedule_arrangement(
            self.get_object(),
            request.user,
            factory_name=request.data.get("factory_name", ""),
            planned_finish_at=request.data.get("planned_finish_at"),
            remark=request.data.get("remark", ""),
        )
        return Response(self.get_serializer(arrangement).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        arrangement = confirm_arrangement(self.get_object(), request.user)
        return Response(self.get_serializer(arrangement).data)

    @action(detail=True, methods=["post"], url_path="mark-exception")
    def mark_exception(self, request, pk=None):
        arrangement = self.get_object()
        arrangement.status = ProductionArrangement.Status.EXCEPTION
        arrangement.remark = request.data.get("remark", arrangement.remark)
        arrangement.save(update_fields=["status", "remark", "updated_at"])
        return Response(self.get_serializer(arrangement).data)
