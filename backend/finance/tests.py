from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from customers.models import Customer
from finance.models import InvoiceRequest


class InvoiceRequestModelTests(TestCase):
    def test_invoice_type_labels_include_tax_rate(self):
        self.assertEqual(InvoiceRequest.InvoiceType.NORMAL.label, "普通13%")
        self.assertEqual(InvoiceRequest.InvoiceType.SPECIAL.label, "专票13%")


class InvoiceRequestApprovalTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username="admin", password="admin123456")
        self.client.force_authenticate(self.user)
        self.customer = Customer.objects.create(name="测试客户", created_by=self.user)

    def create_invoice(self):
        return InvoiceRequest.objects.create(
            request_no="INVTEST001",
            customer=self.customer,
            invoice_type=InvoiceRequest.InvoiceType.NORMAL,
            amount="100.00",
            title="测试抬头",
            applicant=self.user,
            created_by=self.user,
        )

    def test_approve_saves_approval_remark(self):
        invoice = self.create_invoice()

        response = self.client.post(
            f"/api/v1/invoice-requests/{invoice.id}/approve/",
            {"approval_remark": "已核对抬头和金额"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, InvoiceRequest.Status.APPROVED)
        self.assertEqual(invoice.approval_remark, "已核对抬头和金额")
