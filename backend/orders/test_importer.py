import zipfile
from io import BytesIO

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from orders.models import Order


def cell_ref(column_index, row_index):
    letters = ""
    column = column_index + 1
    while column:
        column, remainder = divmod(column - 1, 26)
        letters = chr(65 + remainder) + letters
    return f"{letters}{row_index}"


def build_xlsx(rows):
    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row):
            text = "" if value is None else str(value)
            ref = cell_ref(column_index, row_index)
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>')
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        "</worksheet>"
    )
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    buffer.seek(0)
    buffer.name = "orders.xlsx"
    return buffer


class OrderImportTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="admin123456")
        self.client.force_authenticate(self.admin)
        self.headers = [
            "审批编号",
            "审批状态",
            "审批结果",
            "发起时间",
            "完成时间",
            "客户id",
            "订单号",
            "订单金额",
            "来源店铺",
            "产品类别",
            "是否需要设计",
            "订单说明",
            "收货信息",
            "设计稿/素材",
            "其它说明",
        ]

    def test_admin_can_import_orders_from_xlsx(self):
        file_obj = build_xlsx(
            [
                self.headers,
                [
                    "A001",
                    "完成",
                    "同意",
                    "2021-12-31 17:20:14",
                    "2021-12-31 17:43:31",
                    "韩燕兵-多多-泡泡ktv",
                    "211231-001",
                    "6000",
                    "介知-PDD",
                    "纸巾盒",
                    "是",
                    "抽纸盒-210x105x50mm-5000盒",
                    "韩燕兵 18381753426 四川省南充市",
                    "历史设计稿.ai",
                    "有群",
                ],
                [
                    "A002",
                    "已撤销",
                    "",
                    "2021-12-24 14:43:00",
                    "2021-12-24 14:43:17",
                    "郭旺-多多",
                    "211224-002",
                    "1240",
                    "介知-PDD",
                    "纸巾盒",
                    "否-续订",
                    "方巾盒-2000盒",
                    "郭旺 17301838630 江苏省苏州市",
                    "",
                    "续订",
                ],
            ]
        )
        response = self.client.post("/api/v1/orders/import-spreadsheet/", {"file": file_obj}, format="multipart")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["created"], 2)
        completed = Order.objects.get(platform_order_no="211231-001")
        cancelled = Order.objects.get(platform_order_no="211224-002")
        self.assertEqual(completed.status, Order.Status.COMPLETED)
        self.assertEqual(completed.total_amount, 6000)
        self.assertEqual(completed.customer.name, "韩燕兵-多多-泡泡ktv")
        self.assertEqual(completed.items.first().product_name, "纸巾盒")
        self.assertIn("历史设计稿.ai", completed.remark)
        self.assertNotIn("审批编号", completed.remark)
        self.assertNotIn("A001", completed.remark)
        self.assertEqual(cancelled.status, Order.Status.CANCELLED)
        self.assertEqual(cancelled.design_option.name, "续订无需设计")

    def test_import_skips_duplicate_active_platform_order_no(self):
        file_obj = build_xlsx(
            [
                self.headers,
                ["A001", "完成", "同意", "", "", "客户A", "DUP-001", "100", "介知-PDD", "纸巾盒", "是", "说明", "", "", ""],
            ]
        )
        first = self.client.post("/api/v1/orders/import-spreadsheet/", {"file": file_obj}, format="multipart")
        self.assertEqual(first.status_code, 200)

        file_obj = build_xlsx(
            [
                self.headers,
                ["A002", "完成", "同意", "", "", "客户A", "DUP-001", "100", "介知-PDD", "纸巾盒", "是", "说明", "", "", ""],
            ]
        )
        second = self.client.post("/api/v1/orders/import-spreadsheet/", {"file": file_obj}, format="multipart")

        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["created"], 0)
        self.assertEqual(second.data["skipped"], 1)
        self.assertEqual(Order.objects.filter(platform_order_no="DUP-001").count(), 1)

    def test_dry_run_import_does_not_write_orders(self):
        file_obj = build_xlsx(
            [
                self.headers,
                ["A001", "完成", "同意", "", "", "客户A", "DRY-001", "100", "介知-PDD", "纸巾盒", "是", "说明", "", "", ""],
            ]
        )
        response = self.client.post(
            "/api/v1/orders/import-spreadsheet/",
            {"file": file_obj, "dry_run": "true"},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["dry_run"])
        self.assertEqual(response.data["created"], 1)
        self.assertFalse(Order.objects.filter(platform_order_no="DRY-001").exists())
