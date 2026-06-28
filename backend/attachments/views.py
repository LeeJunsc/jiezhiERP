from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser

from attachments.models import Attachment
from attachments.serializers import AttachmentSerializer


class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        queryset = Attachment.objects.order_by("-created_at")
        business_type = self.request.query_params.get("business_type")
        business_id = self.request.query_params.get("business_id")
        if business_type:
            queryset = queryset.filter(business_type=business_type)
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        return queryset
