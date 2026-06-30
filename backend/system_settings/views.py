from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsAdminRole
from system_settings.models import InvoiceTypeOption, PaymentChannel
from system_settings.serializers import InvoiceTypeOptionSerializer, PaymentChannelSerializer


class PaymentChannelViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentChannelSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        queryset = PaymentChannel.objects.order_by("sort_order", "name")
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset

    def perform_create(self, serializer):
        channel = serializer.save(created_by=self.request.user)
        if channel.is_default:
            PaymentChannel.objects.exclude(pk=channel.pk).update(is_default=False)

    def perform_update(self, serializer):
        channel = serializer.save()
        if channel.is_default:
            PaymentChannel.objects.exclude(pk=channel.pk).update(is_default=False)


class InvoiceTypeOptionViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceTypeOptionSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        queryset = InvoiceTypeOption.objects.order_by("sort_order", "name")
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
