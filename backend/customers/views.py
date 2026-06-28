from django.db.models import Q
from django.db.models.deletion import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsAdminRole, IsSalesOrAdmin
from customers.models import Customer
from customers.serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        if self.action == "destroy":
            return [IsAdminRole()]
        return [IsSalesOrAdmin()]

    def get_queryset(self):
        queryset = Customer.objects.order_by("-created_at")
        keyword = self.request.query_params.get("keyword")
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword)
                | Q(source__icontains=keyword)
                | Q(phone__icontains=keyword)
                | Q(company__icontains=keyword)
                | Q(wechat__icontains=keyword)
                | Q(whatsapp__icontains=keyword)
                | Q(line__icontains=keyword)
                | Q(tags__icontains=keyword)
                | Q(address__icontains=keyword)
                | Q(invoice_title__icontains=keyword)
                | Q(tax_number__icontains=keyword)
                | Q(remark__icontains=keyword)
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ValidationError("该客户已有订单或业务记录，不能直接删除。") from exc
