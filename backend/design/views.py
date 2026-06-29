from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import IsDesignerOrAdmin
from design.models import DesignTask
from design.serializers import DesignTaskSerializer
from design.services import claim_design_task, confirm_design_task


class DesignTaskViewSet(viewsets.ModelViewSet):
    serializer_class = DesignTaskSerializer
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ["claim", "upload_draft", "request_changes", "confirm", "partial_update"]:
            return [IsDesignerOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = DesignTask.objects.select_related("order", "order__store", "order__customer", "order__design_option", "designer").order_by("-created_at")
        status_value = self.request.query_params.get("status")
        if status_value:
            statuses = [status for status in status_value.split(",") if status]
            queryset = queryset.filter(status__in=statuses)
        if self.request.query_params.get("ordering") == "recent_completed":
            queryset = queryset.order_by("-confirmed_at", "-updated_at")
        return queryset

    @action(detail=True, methods=["post"])
    def claim(self, request, pk=None):
        task = claim_design_task(self.get_object(), request.user)
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"], url_path="upload-draft")
    def upload_draft(self, request, pk=None):
        task = self.get_object()
        task.remark = request.data.get("remark", task.remark)
        task.save(update_fields=["remark", "updated_at"])
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"], url_path="request-changes")
    def request_changes(self, request, pk=None):
        task = self.get_object()
        task.status = DesignTask.Status.NEEDS_CHANGES
        task.remark = request.data.get("remark", task.remark)
        task.save(update_fields=["status", "remark", "updated_at"])
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        task = confirm_design_task(self.get_object(), request.user)
        return Response(self.get_serializer(task).data)
