from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from after_sales.models import AfterSalesRequest
from attachments.models import Attachment
from customers.models import Customer
from design.models import DesignTask
from finance.models import InvoiceRequest
from orders.models import DesignOption, Order, OrderItem
from production.models import ProductionArrangement
from stores.models import Store


class OrderFlowTests(TestCase):
    def setUp(self):
        for name in ["销售", "设计", "生产", "管理员"]:
            Group.objects.get_or_create(name=name)
        self.user = User.objects.create_superuser(username="admin", password="admin123456")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.store = Store.objects.create(name="淘宝旗舰店", platform=Store.Platform.TAOBAO, created_by=self.user)
        self.customer = Customer.objects.create(name="陈女士", phone="13800005021", created_by=self.user)
        self.need_design = DesignOption.objects.create(name="新订单需要设计", requires_design=True, sort_order=1, created_by=self.user)
        self.skip_design = DesignOption.objects.create(name="续订无需设计", requires_design=False, sort_order=2, created_by=self.user)

    def create_order(self, design_option):
        order = Order.objects.create(
            order_no=f"JZTEST{Order.objects.count() + 1:04d}",
            store=self.store,
            customer=self.customer,
            salesperson=self.user,
            design_option=design_option,
            total_amount="100.00",
            created_by=self.user,
        )
        OrderItem.objects.create(order=order, product_name="测试商品", quantity=1, unit_price="100.00", line_amount="100.00", created_by=self.user)
        return order

    def order_payload(self, platform_order_no):
        return {
            "platform_order_no": platform_order_no,
            "store": str(self.store.id),
            "customer": str(self.customer.id),
            "salesperson": str(self.user.id),
            "design_option": str(self.need_design.id),
            "total_amount": "100.00",
            "paid_amount": "100.00",
            "payment_status": Order.PaymentStatus.PAID,
            "items": [
                {
                    "product_name": "测试商品",
                    "sku": "SKU-001",
                    "quantity": 1,
                    "unit_price": "100.00",
                    "line_amount": "100.00",
                }
            ],
        }

    def test_submit_order_with_design_creates_design_task(self):
        order = self.create_order(self.need_design)
        response = self.client.post(f"/api/v1/orders/{order.id}/submit/")
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING_DESIGN)
        self.assertTrue(DesignTask.objects.filter(order=order).exists())
        self.assertFalse(ProductionArrangement.objects.filter(order=order).exists())

    def test_duplicate_platform_order_no_rejected_for_active_order(self):
        existing = self.create_order(self.need_design)
        existing.platform_order_no = "TB202606290001"
        existing.status = Order.Status.PENDING_DESIGN
        existing.save(update_fields=["platform_order_no", "status"])

        response = self.client.post("/api/v1/orders/", self.order_payload("TB202606290001"), format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("platform_order_no", response.data)

    def test_duplicate_platform_order_no_allowed_when_existing_order_cancelled(self):
        existing = self.create_order(self.need_design)
        existing.platform_order_no = "TB202606290002"
        existing.status = Order.Status.CANCELLED
        existing.save(update_fields=["platform_order_no", "status"])

        response = self.client.post("/api/v1/orders/", self.order_payload("TB202606290002"), format="json")

        self.assertEqual(response.status_code, 201)

    def test_create_order_requires_core_fields(self):
        payload = self.order_payload("")
        payload["items"] = []
        payload["total_amount"] = "0.00"

        response = self.client.post("/api/v1/orders/", payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("platform_order_no", response.data)

    def test_create_order_requires_product_items(self):
        payload = self.order_payload("TB202606290003")
        payload["items"] = []

        response = self.client.post("/api/v1/orders/", payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("items", response.data)

    def test_design_confirm_creates_production_arrangement(self):
        order = self.create_order(self.need_design)
        self.client.post(f"/api/v1/orders/{order.id}/submit/")
        task = DesignTask.objects.get(order=order)
        self.client.post(f"/api/v1/design-tasks/{task.id}/claim/")
        response = self.client.post(f"/api/v1/design-tasks/{task.id}/confirm/")
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING_PRODUCTION)
        self.assertTrue(ProductionArrangement.objects.filter(order=order).exists())

    def test_submit_order_without_design_creates_production_arrangement(self):
        order = self.create_order(self.skip_design)
        response = self.client.post(f"/api/v1/orders/{order.id}/submit/")
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING_PRODUCTION)
        self.assertFalse(DesignTask.objects.filter(order=order).exists())
        self.assertTrue(ProductionArrangement.objects.filter(order=order).exists())

    def test_confirm_production_arrangement_completes_order(self):
        order = self.create_order(self.skip_design)
        self.client.post(f"/api/v1/orders/{order.id}/submit/")
        arrangement = ProductionArrangement.objects.get(order=order)
        response = self.client.post(f"/api/v1/production-arrangements/{arrangement.id}/confirm/")
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.COMPLETED)
        self.assertIsNotNone(order.completed_at)

    def test_return_production_arrangement_to_design(self):
        order = self.create_order(self.need_design)
        self.client.post(f"/api/v1/orders/{order.id}/submit/")
        task = DesignTask.objects.get(order=order)
        self.client.post(f"/api/v1/design-tasks/{task.id}/claim/")
        self.client.post(f"/api/v1/design-tasks/{task.id}/confirm/")
        arrangement = ProductionArrangement.objects.get(order=order)

        response = self.client.post(
            f"/api/v1/production-arrangements/{arrangement.id}/return-to-design/",
            {"remark": "生产发现设计尺寸需调整"},
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        arrangement.refresh_from_db()
        task.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING_DESIGN)
        self.assertEqual(arrangement.status, ProductionArrangement.Status.EXCEPTION)
        self.assertEqual(task.status, DesignTask.Status.NEEDS_CHANGES)

    def test_reconfirm_returned_design_reopens_production_arrangement(self):
        order = self.create_order(self.need_design)
        self.client.post(f"/api/v1/orders/{order.id}/submit/")
        task = DesignTask.objects.get(order=order)
        self.client.post(f"/api/v1/design-tasks/{task.id}/claim/")
        self.client.post(f"/api/v1/design-tasks/{task.id}/confirm/")
        arrangement = ProductionArrangement.objects.get(order=order)
        self.client.post(f"/api/v1/production-arrangements/{arrangement.id}/return-to-design/")

        task.refresh_from_db()
        response = self.client.post(f"/api/v1/design-tasks/{task.id}/confirm/")

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        arrangement.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING_PRODUCTION)
        self.assertEqual(arrangement.status, ProductionArrangement.Status.PENDING)

    def test_reject_production_arrangement_cancels_order(self):
        order = self.create_order(self.skip_design)
        self.client.post(f"/api/v1/orders/{order.id}/submit/")
        arrangement = ProductionArrangement.objects.get(order=order)

        response = self.client.post(
            f"/api/v1/production-arrangements/{arrangement.id}/reject-order/",
            {"remark": "工厂无法生产"},
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        arrangement.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(arrangement.status, ProductionArrangement.Status.EXCEPTION)

    def test_full_business_flow_from_order_to_after_sales(self):
        payload = self.order_payload("TB-FULL-FLOW-001")
        create_response = self.client.post("/api/v1/orders/", payload, format="json")
        self.assertEqual(create_response.status_code, 201)
        order_id = create_response.data["id"]

        duplicate_response = self.client.post("/api/v1/orders/", payload, format="json")
        self.assertEqual(duplicate_response.status_code, 400)
        self.assertIn("platform_order_no", duplicate_response.data)

        submit_response = self.client.post(f"/api/v1/orders/{order_id}/submit/")
        self.assertEqual(submit_response.status_code, 200)
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, Order.Status.PENDING_DESIGN)

        task = DesignTask.objects.get(order=order)
        claim_response = self.client.post(f"/api/v1/design-tasks/{task.id}/claim/")
        self.assertEqual(claim_response.status_code, 200)
        self.assertEqual(claim_response.data["status"], DesignTask.Status.DESIGNING)

        design_file = SimpleUploadedFile("design-final.txt", b"design file", content_type="text/plain")
        design_upload_response = self.client.post(
            "/api/v1/attachments/",
            {"file": design_file, "business_type": "design", "business_id": str(task.id)},
            format="multipart",
        )
        self.assertEqual(design_upload_response.status_code, 201)

        design_confirm_response = self.client.post(f"/api/v1/design-tasks/{task.id}/confirm/")
        self.assertEqual(design_confirm_response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING_PRODUCTION)

        arrangement = ProductionArrangement.objects.get(order=order)
        schedule_response = self.client.post(
            f"/api/v1/production-arrangements/{arrangement.id}/schedule/",
            {"factory_name": "测试代工厂", "remark": "正常排产"},
            format="json",
        )
        self.assertEqual(schedule_response.status_code, 200)
        self.assertEqual(schedule_response.data["status"], ProductionArrangement.Status.SCHEDULED)

        production_file = SimpleUploadedFile("production-note.txt", b"production file", content_type="text/plain")
        production_upload_response = self.client.post(
            "/api/v1/attachments/",
            {"file": production_file, "business_type": "production", "business_id": str(arrangement.id)},
            format="multipart",
        )
        self.assertEqual(production_upload_response.status_code, 201)

        production_confirm_response = self.client.post(f"/api/v1/production-arrangements/{arrangement.id}/confirm/")
        self.assertEqual(production_confirm_response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.COMPLETED)

        invoice_response = self.client.post(
            "/api/v1/invoice-requests/",
            {
                "order": str(order.id),
                "invoice_type": InvoiceRequest.InvoiceType.NORMAL,
                "amount": "100.00",
                "title": "陈女士",
                "tax_number": "91310000TEST",
                "remark": "完整流程测试发票",
            },
            format="json",
        )
        self.assertEqual(invoice_response.status_code, 201)
        invoice_id = invoice_response.data["id"]

        invoice_file = SimpleUploadedFile("invoice.pdf", b"invoice file", content_type="application/pdf")
        invoice_upload_response = self.client.post(
            "/api/v1/attachments/",
            {"file": invoice_file, "business_type": "invoice", "business_id": invoice_id},
            format="multipart",
        )
        self.assertEqual(invoice_upload_response.status_code, 201)

        invoice_approve_response = self.client.post(f"/api/v1/invoice-requests/{invoice_id}/approve/")
        self.assertEqual(invoice_approve_response.status_code, 200)
        self.assertEqual(invoice_approve_response.data["status"], InvoiceRequest.Status.APPROVED)

        after_sales_response = self.client.post(
            "/api/v1/after-sales-requests/",
            {
                "order": str(order.id),
                "type": AfterSalesRequest.Type.RESHIP,
                "description": "完整流程测试售后证据",
                "refund_amount": "0.00",
            },
            format="json",
        )
        self.assertEqual(after_sales_response.status_code, 201)
        after_sales_id = after_sales_response.data["id"]

        after_sales_file = SimpleUploadedFile("after-sales-evidence.txt", b"after sales file", content_type="text/plain")
        after_sales_upload_response = self.client.post(
            "/api/v1/attachments/",
            {"file": after_sales_file, "business_type": "after_sales", "business_id": after_sales_id},
            format="multipart",
        )
        self.assertEqual(after_sales_upload_response.status_code, 201)

        complete_after_sales_response = self.client.post(
            f"/api/v1/after-sales-requests/{after_sales_id}/complete/",
            {"remark": "补发快递单号 SF123456"},
            format="json",
        )
        self.assertEqual(complete_after_sales_response.status_code, 200)
        self.assertEqual(complete_after_sales_response.data["status"], AfterSalesRequest.Status.COMPLETED)
        self.assertEqual(complete_after_sales_response.data["remark"], "补发快递单号 SF123456")

        related_response = self.client.get(f"/api/v1/orders/{order.id}/related/")
        self.assertEqual(related_response.status_code, 200)
        self.assertEqual(len(related_response.data["design_attachments"]), 1)
        self.assertEqual(len(related_response.data["production_attachments"]), 1)
        self.assertEqual(len(related_response.data["invoice_requests"]), 1)
        self.assertEqual(len(related_response.data["invoice_requests"][0]["attachments"]), 1)
        self.assertEqual(len(related_response.data["after_sales_requests"]), 1)
        self.assertEqual(len(related_response.data["after_sales_requests"][0]["attachments"]), 1)
        self.assertEqual(related_response.data["after_sales_requests"][0]["remark"], "补发快递单号 SF123456")

    def test_reject_after_sales_request_saves_remark(self):
        order = self.create_order(self.skip_design)
        after_sales = AfterSalesRequest.objects.create(
            request_no="ASTEST001",
            order=order,
            type=AfterSalesRequest.Type.COMPLAINT,
            description="客户投诉包装破损",
            created_by=self.user,
        )

        response = self.client.post(
            f"/api/v1/after-sales-requests/{after_sales.id}/reject/",
            {"remark": "证据不足，驳回申请"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        after_sales.refresh_from_db()
        self.assertEqual(after_sales.status, AfterSalesRequest.Status.CLOSED)
        self.assertEqual(after_sales.remark, "证据不足，驳回申请")
        self.assertEqual(Attachment.objects.filter(business_id=order.id).count(), 0)

    def test_cancelled_order_cannot_be_submitted(self):
        order = self.create_order(self.need_design)
        self.client.post(f"/api/v1/orders/{order.id}/cancel/")
        response = self.client.post(f"/api/v1/orders/{order.id}/submit/")
        self.assertEqual(response.status_code, 400)
