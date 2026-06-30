from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from system_settings.models import InvoiceTypeOption


class InvoiceTypeOptionTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="admin123456")
        self.client.force_authenticate(self.admin)

    def test_list_enabled_invoice_type_options(self):
        InvoiceTypeOption.objects.create(name="普通13%", code="normal", tax_rate="13.00", sort_order=10, created_by=self.admin)
        InvoiceTypeOption.objects.create(
            name="停用类型",
            code="disabled",
            tax_rate="6.00",
            sort_order=20,
            status=InvoiceTypeOption.Status.DISABLED,
            created_by=self.admin,
        )

        response = self.client.get("/api/v1/invoice-type-options/", {"status": "enabled"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "普通13%")
        self.assertEqual(response.data["results"][0]["code"], "normal")
