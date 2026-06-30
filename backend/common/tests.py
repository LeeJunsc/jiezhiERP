from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.utils import timezone
from rest_framework.test import APITestCase

from after_sales.models import AfterSalesRequest
from customers.models import Customer
from finance.models import InvoiceRequest
from orders.models import DesignOption, Order
from stores.models import Store


class DashboardKanbanPermissionTests(APITestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.sales = self.create_user("sales01", "销售")
        self.other_sales = self.create_user("sales02", "销售")
        self.designer = self.create_user("design01", "设计")
        self.production = self.create_user("prod01", "生产")
        self.finance = self.create_user("finance01", "财务")
        self.after_sales = self.create_user("aftersales01", "售后")
        self.admin = self.create_user("admin01", "管理员")

        self.customer = Customer.objects.create(name="客户A")
        self.store = Store.objects.create(name="测试店铺", platform=Store.Platform.TAOBAO, owner=self.sales)
        self.design_option = DesignOption.objects.create(name="新订单需要设计", requires_design=True)

        self.sales_order = self.create_order("JZTEST001", self.sales, "100.00", Order.Status.PENDING_DESIGN)
        self.sales_old_order = self.create_order("JZTEST000", self.sales, "50.00", Order.Status.COMPLETED, days_ago=2)
        self.other_order = self.create_order("JZTEST002", self.other_sales, "900.00", Order.Status.PENDING_PRODUCTION)

        AfterSalesRequest.objects.create(
            request_no="AS001",
            order=self.sales_order,
            type=AfterSalesRequest.Type.OTHER,
            status=AfterSalesRequest.Status.PENDING,
            description="销售自己的售后",
        )
        AfterSalesRequest.objects.create(
            request_no="AS002",
            order=self.other_order,
            type=AfterSalesRequest.Type.OTHER,
            status=AfterSalesRequest.Status.PENDING,
            description="其他销售售后",
        )
        InvoiceRequest.objects.create(
            request_no="INV001",
            order=self.sales_order,
            customer=self.customer,
            amount=Decimal("100.00"),
            title="客户A",
            status=InvoiceRequest.Status.PENDING,
            applicant=self.sales,
        )

    def create_user(self, username, role):
        group, _ = Group.objects.get_or_create(name=role)
        user = User.objects.create_user(username=username, password="demo123456")
        user.groups.add(group)
        return user

    def create_order(self, order_no, salesperson, amount, status, days_ago=0):
        order = Order.objects.create(
            order_no=order_no,
            platform_order_no=order_no,
            store=self.store,
            customer=self.customer,
            salesperson=salesperson,
            design_option=self.design_option,
            status=status,
            total_amount=Decimal(amount),
            paid_amount=Decimal(amount),
            payment_status=Order.PaymentStatus.PAID,
        )
        if days_ago:
            Order.objects.filter(pk=order.pk).update(created_at=timezone.now() - timezone.timedelta(days=days_ago))
            order.refresh_from_db()
        return order

    def get_kanban(self, user):
        self.client.force_authenticate(user)
        response = self.client.get(
            "/api/v1/dashboard/kanban",
            {"start_date": self.today.isoformat(), "end_date": self.today.isoformat()},
        )
        self.assertEqual(response.status_code, 200)
        return response.data

    def test_sales_dashboard_only_returns_own_scoped_metrics(self):
        data = self.get_kanban(self.sales)
        self.assertEqual(
            data["visible_metrics"],
            [
                "amount",
                "order_count",
                "returning_customer_order_count",
                "pending_design_order_count",
                "pending_production_order_count",
                "pending_invoice_count",
                "after_sales_order_count",
            ],
        )
        self.assertEqual(data["summary"]["amount"], "100.00")
        self.assertEqual(data["summary"]["order_count"], 1)
        self.assertEqual(data["summary"]["pending_design_order_count"], 1)
        self.assertEqual(data["summary"]["pending_production_order_count"], 0)
        self.assertEqual(data["summary"]["pending_invoice_count"], 1)
        self.assertEqual(data["summary"]["after_sales_order_count"], 1)

    def test_role_dashboards_only_return_allowed_metric_keys(self):
        expected = {
            self.designer: ["pending_design_order_count", "after_sales_order_count"],
            self.production: ["pending_production_order_count", "after_sales_order_count"],
            self.after_sales: ["order_count", "after_sales_order_count"],
        }
        for user, metrics in expected.items():
            data = self.get_kanban(user)
            self.assertEqual(data["visible_metrics"], metrics)
            self.assertEqual(set(data["summary"].keys()), set(metrics))
            self.assertEqual(set(data["series"][0].keys()), {"date", *metrics})

    def test_admin_and_finance_dashboards_return_all_metrics(self):
        for user in [self.admin, self.finance]:
            data = self.get_kanban(user)
            self.assertEqual(
                data["visible_metrics"],
                [
                    "amount",
                    "order_count",
                    "returning_customer_order_count",
                    "after_sales_order_count",
                    "pending_design_order_count",
                    "pending_production_order_count",
                    "pending_invoice_count",
                ],
            )
            self.assertEqual(data["summary"]["order_count"], 2)
            self.assertEqual(data["summary"]["after_sales_order_count"], 2)
