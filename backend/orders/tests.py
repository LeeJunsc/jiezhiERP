from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework.test import APIClient

from customers.models import Customer
from design.models import DesignTask
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

    def test_submit_order_with_design_creates_design_task(self):
        order = self.create_order(self.need_design)
        response = self.client.post(f"/api/v1/orders/{order.id}/submit/")
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING_DESIGN)
        self.assertTrue(DesignTask.objects.filter(order=order).exists())
        self.assertFalse(ProductionArrangement.objects.filter(order=order).exists())

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

    def test_cancelled_order_cannot_be_submitted(self):
        order = self.create_order(self.need_design)
        self.client.post(f"/api/v1/orders/{order.id}/cancel/")
        response = self.client.post(f"/api/v1/orders/{order.id}/submit/")
        self.assertEqual(response.status_code, 400)
