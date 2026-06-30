from django.contrib.auth.models import Group, Permission, User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from after_sales.models import AfterSalesRequest
from accounts.permission_catalog import split_permission_code
from attachments.models import Attachment
from customers.models import Customer
from design.models import DesignTask
from finance.models import InvoiceRequest
from orders.models import DesignOption, Order, OrderItem
from production.models import ProductionArrangement
from stores.models import Store
from system_settings.models import PaymentChannel


class Command(BaseCommand):
    help = "初始化管理员、角色、设计处理方式和演示业务数据。"

    def demo_datetime(self, number, prefix_length=2):
        date_text = number[prefix_length : prefix_length + 8]
        naive = timezone.datetime.strptime(date_text, "%Y%m%d").replace(hour=10, minute=0)
        return timezone.make_aware(naive)

    def create_demo_attachment(self, *, business_type, business_id, file_name, content, uploader):
        attachment, created = Attachment.objects.get_or_create(
            business_type=business_type,
            business_id=business_id,
            file_name=file_name,
            defaults={
                "file_type": "text/plain",
                "file_size": len(content.encode("utf-8")),
                "uploader": uploader,
                "created_by": uploader,
            },
        )
        if created or not attachment.file:
            attachment.file.save(file_name, ContentFile(content.encode("utf-8")), save=True)
        return attachment

    def handle(self, *args, **options):
        roles = ["销售", "设计", "生产", "财务", "售后", "管理员"]
        groups = {name: Group.objects.get_or_create(name=name)[0] for name in roles}

        role_permissions = {
            "销售": [
                "orders.view_order",
                "orders.add_order",
                "orders.change_order",
                "customers.view_customer",
                "customers.add_customer",
                "customers.change_customer",
                "stores.view_store",
                "orders.view_designoption",
                "system_settings.view_paymentchannel",
                "attachments.view_attachment",
                "attachments.add_attachment",
                "after_sales.view_aftersalesrequest",
                "after_sales.change_aftersalesrequest",
            ],
            "设计": [
                "orders.view_order",
                "customers.view_customer",
                "design.view_designtask",
                "design.change_designtask",
                "attachments.view_attachment",
                "attachments.add_attachment",
            ],
            "生产": [
                "orders.view_order",
                "customers.view_customer",
                "production.view_productionarrangement",
                "production.change_productionarrangement",
                "attachments.view_attachment",
                "attachments.add_attachment",
            ],
            "财务": [
                "orders.view_order",
                "customers.view_customer",
                "finance.view_invoicerequest",
                "finance.change_invoicerequest",
                "system_settings.view_paymentchannel",
            ],
            "售后": [
                "orders.view_order",
                "customers.view_customer",
                "after_sales.view_aftersalesrequest",
                "after_sales.change_aftersalesrequest",
                "attachments.view_attachment",
                "attachments.add_attachment",
            ],
        }
        all_configured_permissions = set()
        for codes in role_permissions.values():
            all_configured_permissions.update(codes)
        role_permissions["管理员"] = list(all_configured_permissions) + [
            "orders.delete_order",
            "customers.delete_customer",
            "stores.change_store",
            "orders.change_designoption",
            "system_settings.change_paymentchannel",
            "attachments.delete_attachment",
            "auth.view_user",
            "auth.add_user",
            "auth.change_user",
            "auth.delete_user",
            "auth.view_group",
            "auth.add_group",
            "auth.change_group",
            "auth.delete_group",
        ]
        for role, codes in role_permissions.items():
            permissions = []
            for code in codes:
                app_label, codename = split_permission_code(code)
                try:
                    permissions.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
                except Permission.DoesNotExist:
                    continue
            groups[role].permissions.set(permissions)

        admin, _ = User.objects.get_or_create(username="admin", defaults={"is_staff": True, "is_superuser": True})
        admin.is_staff = True
        admin.is_superuser = True
        admin.first_name = "系统管理员"
        admin.set_password("admin123456")
        admin.save()
        admin.groups.add(groups["管理员"])

        options_data = [
            ("新订单需要设计", True, 10, "新定制订单，需要完整设计稿"),
            ("老订单修改", True, 20, "基于历史订单修改尺寸、文字、图案等"),
            ("仅标注", True, 30, "不需要完整设计稿，但需要设计人员标注生产说明"),
            ("续订无需设计", False, 40, "复购或续订，直接进入生产安排"),
        ]
        for name, requires_design, sort_order, description in options_data:
            DesignOption.objects.update_or_create(
                name=name,
                defaults={
                    "requires_design": requires_design,
                    "sort_order": sort_order,
                    "description": description,
                    "created_by": admin,
                },
            )

        channels_data = [
            ("平台", "platform", True, 10),
            ("支付宝", "alipay", False, 20),
            ("微信", "wechat", False, 30),
            ("银行转账", "bank_transfer", False, 40),
            ("PayPal", "paypal", False, 50),
            ("其它", "other", False, 60),
        ]
        for name, code, is_default, sort_order in channels_data:
            PaymentChannel.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "is_default": is_default,
                    "sort_order": sort_order,
                    "status": PaymentChannel.Status.ENABLED,
                    "created_by": admin,
                },
            )
        PaymentChannel.objects.filter(code="platform").update(is_default=True)
        PaymentChannel.objects.exclude(code="platform").update(is_default=False)
        platform_channel = PaymentChannel.objects.get(code="platform")

        users_data = [
            ("sales01", "李销售", "销售"),
            ("design01", "王设计", "设计"),
            ("prod01", "赵生产", "生产"),
            ("finance01", "钱财务", "财务"),
            ("aftersales01", "孙售后", "售后"),
            ("admin01", "测试管理员", "管理员"),
        ]
        users = {"admin": admin}
        for username, first_name, role in users_data:
            user, _ = User.objects.get_or_create(username=username, defaults={"first_name": first_name, "is_active": True})
            user.first_name = first_name
            user.is_active = True
            user.set_password("demo123456")
            user.save()
            user.groups.clear()
            user.groups.add(groups[role])
            users[username] = user

        stores = {}
        stores_data = [
            ("淘宝旗舰店", Store.Platform.TAOBAO, "sales01"),
            ("抖音定制店", Store.Platform.DOUYIN, "sales01"),
            ("小红书买手店", Store.Platform.XIAOHONGSHU, "sales01"),
            ("拼多多工厂店", Store.Platform.PINDUODUO, "sales01"),
        ]
        for name, platform, owner_key in stores_data:
            store, _ = Store.objects.update_or_create(
                name=name,
                defaults={"platform": platform, "owner": users[owner_key], "status": Store.Status.ENABLED, "created_by": admin},
            )
            stores[name] = store

        customers = {}
        customers_data = [
            ("陈女士", "淘宝", "个人客户", "13800005021", "chen-demo", "", "", "高复购,加急", "上海市浦东新区", "个人抬头"),
            ("明辰贸易", "抖音", "上海明辰贸易有限公司", "02188889999", "mingchen", "", "", "企业客户,专票", "上海市闵行区", "上海明辰贸易有限公司"),
            ("周先生", "小红书", "个人客户", "13900001888", "zhou-demo", "", "", "安装敏感", "杭州市西湖区", ""),
            ("星禾设计", "淘宝", "苏州星禾设计有限公司", "18600006666", "xinghe-design", "", "", "长期客户", "苏州市工业园区", "苏州星禾设计有限公司"),
            ("林小姐", "拼多多", "个人客户", "13700001234", "lin-demo", "", "", "婚礼订单", "广州市天河区", ""),
            ("北川文创", "抖音", "北京北川文创有限公司", "01066668888", "beichuan", "", "", "文创,大客户", "北京市朝阳区", "北京北川文创有限公司"),
            ("南风礼品", "淘宝", "深圳南风礼品有限公司", "075512345678", "nanfeng", "+8613800012345", "", "礼品,复购", "深圳市南山区", "深圳南风礼品有限公司"),
            ("海棠工作室", "小红书", "海棠工作室", "18500002345", "haitang", "", "haitang-line", "设计师客户", "成都市高新区", ""),
        ]
        for name, source, company, phone, wechat, whatsapp, line, tags, address, invoice_title in customers_data:
            customer, _ = Customer.objects.update_or_create(
                name=name,
                defaults={
                    "source": source,
                    "company": company,
                    "phone": phone,
                    "wechat": wechat,
                    "whatsapp": whatsapp,
                    "line": line,
                    "tags": tags,
                    "address": address,
                    "invoice_title": invoice_title,
                    "created_by": admin,
                },
            )
            customers[name] = customer

        design_options = {option.name: option for option in DesignOption.objects.all()}
        now = timezone.now()

        orders_data = [
            {
                "order_no": "JZ20260628001",
                "platform_order_no": "TB202606280001",
                "store": "淘宝旗舰店",
                "customer": "陈女士",
                "design_option": "新订单需要设计",
                "status": Order.Status.PENDING_DESIGN,
                "amount": "2680.00",
                "paid": "0.00",
                "payment_status": Order.PaymentStatus.UNPAID,
                "urgent": True,
                "delivery_days": 7,
                "note": "透明亚克力展示架，LOGO 丝印，需先出设计稿确认。",
                "item": ("定制亚克力展示架", 20, "134.00", "透明", "30x20cm"),
                "design": DesignTask.Status.PENDING,
            },
            {
                "order_no": "JZ20260628002",
                "platform_order_no": "DY202606280118",
                "store": "抖音定制店",
                "customer": "明辰贸易",
                "design_option": "续订无需设计",
                "status": Order.Status.PENDING_PRODUCTION,
                "amount": "8600.00",
                "paid": "8600.00",
                "payment_status": Order.PaymentStatus.PAID,
                "urgent": False,
                "delivery_days": 10,
                "note": "老款礼盒续订，按上次文件生产，无需重新设计。",
                "item": ("品牌定制礼盒", 200, "43.00", "深蓝", "22x16x8cm"),
                "production": ProductionArrangement.Status.PENDING,
                "factory": "",
            },
            {
                "order_no": "JZ20260627018",
                "platform_order_no": "XHS202606270618",
                "store": "小红书买手店",
                "customer": "周先生",
                "design_option": "仅标注",
                "status": Order.Status.DESIGNING,
                "amount": "1290.00",
                "paid": "500.00",
                "payment_status": Order.PaymentStatus.PARTIAL,
                "urgent": True,
                "delivery_days": 4,
                "note": "照片墙装饰板，仅需标注孔位和安装方向。",
                "item": ("定制照片墙装饰板", 6, "215.00", "原木色", "60x40cm"),
                "design": DesignTask.Status.DESIGNING,
            },
            {
                "order_no": "JZ20260626009",
                "platform_order_no": "TB202606260339",
                "store": "淘宝旗舰店",
                "customer": "星禾设计",
                "design_option": "老订单修改",
                "status": Order.Status.COMPLETED,
                "amount": "4200.00",
                "paid": "4200.00",
                "payment_status": Order.PaymentStatus.PAID,
                "urgent": False,
                "delivery_days": -1,
                "note": "展会桌牌复购，文字内容小幅调整。",
                "item": ("亚克力桌牌", 120, "35.00", "透明", "18x6cm"),
                "design": DesignTask.Status.CONFIRMED,
                "production": ProductionArrangement.Status.CONFIRMED,
                "factory": "启明工厂",
            },
            {
                "order_no": "JZ20260625012",
                "platform_order_no": "PDD202606250099",
                "store": "拼多多工厂店",
                "customer": "林小姐",
                "design_option": "新订单需要设计",
                "status": Order.Status.DRAFT,
                "amount": "780.00",
                "paid": "0.00",
                "payment_status": Order.PaymentStatus.UNPAID,
                "urgent": False,
                "delivery_days": 12,
                "note": "婚礼席位牌，客户素材待补充。",
                "item": ("婚礼席位牌", 30, "26.00", "奶白", "10x8cm"),
            },
            {
                "order_no": "JZ20260624021",
                "platform_order_no": "DY202606240721",
                "store": "抖音定制店",
                "customer": "北川文创",
                "design_option": "新订单需要设计",
                "status": Order.Status.DESIGN_CONFIRMED,
                "amount": "15600.00",
                "paid": "8000.00",
                "payment_status": Order.PaymentStatus.PARTIAL,
                "urgent": False,
                "delivery_days": 14,
                "note": "博物馆文创展示架，设计稿已确认，等待生产安排。",
                "item": ("文创展示架", 80, "195.00", "黑色", "45x30cm"),
                "design": DesignTask.Status.CONFIRMED,
            },
            {
                "order_no": "JZ20260623006",
                "platform_order_no": "TB202606230456",
                "store": "淘宝旗舰店",
                "customer": "南风礼品",
                "design_option": "续订无需设计",
                "status": Order.Status.PENDING_PRODUCTION,
                "amount": "9800.00",
                "paid": "9800.00",
                "payment_status": Order.PaymentStatus.PAID,
                "urgent": True,
                "delivery_days": 5,
                "note": "企业周年礼品续订，按历史文件生产。",
                "item": ("企业纪念钥匙扣", 500, "19.60", "银色", "常规"),
                "production": ProductionArrangement.Status.SCHEDULED,
                "factory": "华东代工厂",
            },
            {
                "order_no": "JZ20260622015",
                "platform_order_no": "XHS202606220315",
                "store": "小红书买手店",
                "customer": "海棠工作室",
                "design_option": "仅标注",
                "status": Order.Status.CANCELLED,
                "amount": "660.00",
                "paid": "0.00",
                "payment_status": Order.PaymentStatus.UNPAID,
                "urgent": False,
                "delivery_days": 8,
                "note": "客户取消，保留记录用于追溯。",
                "item": ("定制桌面立牌", 12, "55.00", "透明", "A5"),
            },
            {
                "order_no": "JZ20260621003",
                "platform_order_no": "PDD202606210103",
                "store": "拼多多工厂店",
                "customer": "明辰贸易",
                "design_option": "老订单修改",
                "status": Order.Status.PENDING_PRODUCTION,
                "amount": "3200.00",
                "paid": "1200.00",
                "payment_status": Order.PaymentStatus.PARTIAL,
                "urgent": False,
                "delivery_days": 9,
                "note": "旧款标签牌改色，设计已确认，待安排工厂。",
                "item": ("定制标签牌", 100, "32.00", "灰色", "12x5cm"),
                "design": DesignTask.Status.CONFIRMED,
                "production": ProductionArrangement.Status.PENDING,
                "factory": "",
            },
            {
                "order_no": "JZ20260620008",
                "platform_order_no": "DY202606200208",
                "store": "抖音定制店",
                "customer": "陈女士",
                "design_option": "新订单需要设计",
                "status": Order.Status.COMPLETED,
                "amount": "1880.00",
                "paid": "1880.00",
                "payment_status": Order.PaymentStatus.PAID,
                "urgent": False,
                "delivery_days": -3,
                "note": "宠物纪念相框，已安排工厂并完成订单。",
                "item": ("宠物纪念相框", 4, "470.00", "胡桃木", "30x30cm"),
                "design": DesignTask.Status.CONFIRMED,
                "production": ProductionArrangement.Status.CONFIRMED,
                "factory": "南方工艺厂",
            },
        ]

        for data in orders_data:
            order, _ = Order.objects.update_or_create(
                order_no=data["order_no"],
                defaults={
                    "platform_order_no": data["platform_order_no"],
                    "store": stores[data["store"]],
                    "customer": customers[data["customer"]],
                    "salesperson": users["sales01"],
                    "design_option": design_options[data["design_option"]],
                    "status": data["status"],
                    "total_amount": data["amount"],
                    "paid_amount": data["paid"],
                    "payment_status": data["payment_status"],
                    "payment_channel": platform_channel,
                    "delivery_date": timezone.localdate() + timezone.timedelta(days=data["delivery_days"]),
                    "urgent": data["urgent"],
                    "customization_note": data["note"],
                    "submitted_at": now if data["status"] != Order.Status.DRAFT else None,
                    "completed_at": now if data["status"] == Order.Status.COMPLETED else None,
                    "created_by": admin,
                },
            )
            created_at = self.demo_datetime(data["order_no"])
            Order.objects.filter(pk=order.pk).update(created_at=created_at, updated_at=created_at)
            product_name, quantity, unit_price, color, size = data["item"]
            OrderItem.objects.update_or_create(
                order=order,
                product_name=product_name,
                defaults={
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_amount": data["amount"],
                    "custom_color": color,
                    "custom_size": size,
                    "created_by": admin,
                },
            )
            if data.get("design"):
                design_task, _ = DesignTask.objects.update_or_create(
                    order=order,
                    defaults={
                        "task_no": data["order_no"].replace("JZ", "JZD", 1),
                        "designer": users["design01"] if data["design"] != DesignTask.Status.PENDING else None,
                        "status": data["design"],
                        "confirmed_at": now if data["design"] == DesignTask.Status.CONFIRMED else None,
                        "remark": "演示设计任务",
                        "created_by": admin,
                    },
                )
                DesignTask.objects.filter(pk=design_task.pk).update(created_at=created_at, updated_at=created_at)
            if data.get("production"):
                arrangement, _ = ProductionArrangement.objects.update_or_create(
                    order=order,
                    defaults={
                        "arrangement_no": data["order_no"].replace("JZ", "JZP", 1),
                        "owner": users["prod01"],
                        "factory_name": data.get("factory", ""),
                        "status": data["production"],
                        "planned_finish_at": now + timezone.timedelta(days=max(data["delivery_days"], 1)),
                        "confirmed_at": now if data["production"] == ProductionArrangement.Status.CONFIRMED else None,
                        "remark": "演示生产安排",
                        "created_by": admin,
                    },
                )
                ProductionArrangement.objects.filter(pk=arrangement.pk).update(created_at=created_at, updated_at=created_at)

        orders = {order.order_no: order for order in Order.objects.filter(order_no__startswith="JZ202606")}
        invoice_data = [
            ("INV20260628001", "JZ20260628001", "陈女士", InvoiceRequest.InvoiceType.NORMAL, "2680.00", InvoiceRequest.Status.PENDING),
            ("INV20260627005", "JZ20260624021", "北川文创", InvoiceRequest.InvoiceType.SPECIAL, "15600.00", InvoiceRequest.Status.PENDING),
            ("INV20260626003", "JZ20260626009", "星禾设计", InvoiceRequest.InvoiceType.SPECIAL, "4200.00", InvoiceRequest.Status.APPROVED),
            ("INV20260623002", "JZ20260623006", "南风礼品", InvoiceRequest.InvoiceType.NORMAL, "9800.00", InvoiceRequest.Status.REJECTED),
        ]
        for request_no, order_no, customer_name, invoice_type, amount, status in invoice_data:
            invoice, _ = InvoiceRequest.objects.update_or_create(
                request_no=request_no,
                defaults={
                    "order": orders.get(order_no),
                    "customer": customers[customer_name],
                    "invoice_type": invoice_type,
                    "amount": amount,
                    "title": customers[customer_name].invoice_title or customer_name,
                    "tax_number": "91310000DEMO8888" if invoice_type == InvoiceRequest.InvoiceType.SPECIAL else "",
                    "status": status,
                    "applicant": users["sales01"],
                    "approver": users["finance01"] if status != InvoiceRequest.Status.PENDING else None,
                    "created_by": admin,
                },
            )
            invoice_created_at = self.demo_datetime(request_no, prefix_length=3)
            InvoiceRequest.objects.filter(pk=invoice.pk).update(created_at=invoice_created_at, updated_at=invoice_created_at)

        after_sales_data = [
            ("AS20260628003", "JZ20260620008", AfterSalesRequest.Type.RESHIP, AfterSalesRequest.Status.PENDING, "客户反馈边角轻微划痕，申请补发一个配件。", ""),
            ("AS20260627002", "JZ20260626009", AfterSalesRequest.Type.REFUND, AfterSalesRequest.Status.PROCESSING, "桌牌数量少 2 个，客户申请部分退款。", "财务核对后处理"),
            ("AS20260625001", "JZ20260623006", AfterSalesRequest.Type.COMPLAINT, AfterSalesRequest.Status.COMPLETED, "客户反馈物流延迟，已补偿优惠券。", "已完成安抚"),
        ]
        for request_no, order_no, case_type, status, description, solution in after_sales_data:
            after_sale, _ = AfterSalesRequest.objects.update_or_create(
                request_no=request_no,
                defaults={
                    "order": orders[order_no],
                    "type": case_type,
                    "status": status,
                    "description": description,
                    "solution": solution,
                    "refund_amount": "320.00" if case_type == AfterSalesRequest.Type.REFUND else None,
                    "owner": users["sales01"],
                    "created_by": admin,
                },
            )
            after_sale_created_at = self.demo_datetime(request_no, prefix_length=2)
            AfterSalesRequest.objects.filter(pk=after_sale.pk).update(created_at=after_sale_created_at, updated_at=after_sale_created_at)

        demo_attachment_data = [
            ("order", "JZ20260628001", "客户原始需求说明.txt", "客户提供的尺寸、LOGO位置、材质要求。"),
            ("order", "JZ20260626009", "订单素材清单.txt", "客户确认的桌牌名单与排版要求。"),
            ("design", "JZ20260626009", "设计定稿说明.txt", "设计定稿：亚克力桌牌版式已确认，可进入生产。"),
            ("design", "JZ20260623006", "设计最终版.txt", "设计定稿：礼品套装外盒与内托结构确认。"),
            ("production", "JZ20260623006", "生产交接说明.txt", "生产安排：华东代工厂，按确认稿生产。"),
            ("invoice", "INV20260626003", "电子发票文件.txt", "发票附件：星禾设计专票演示文件。"),
            ("invoice", "INV20260623002", "驳回原因附件.txt", "发票附件：抬头信息不完整，需销售重新确认。"),
            ("after_sales", "AS20260627002", "售后证据说明.txt", "客户反馈少发 2 个桌牌，附核对说明。"),
            ("after_sales", "AS20260625001", "售后处理凭证.txt", "售后处理：已补偿优惠券，客户确认。"),
        ]
        for business_type, identifier, file_name, content in demo_attachment_data:
            business_id = None
            if business_type == "order" and identifier in orders:
                business_id = orders[identifier].id
            elif business_type == "design" and identifier in orders and hasattr(orders[identifier], "design_task"):
                business_id = orders[identifier].design_task.id
            elif business_type == "production" and identifier in orders and hasattr(orders[identifier], "production_arrangement"):
                business_id = orders[identifier].production_arrangement.id
            elif business_type == "invoice":
                invoice = InvoiceRequest.objects.filter(request_no=identifier).first()
                business_id = invoice.id if invoice else None
            elif business_type == "after_sales":
                after_sale = AfterSalesRequest.objects.filter(request_no=identifier).first()
                business_id = after_sale.id if after_sale else None
            if business_id:
                self.create_demo_attachment(
                    business_type=business_type,
                    business_id=business_id,
                    file_name=file_name,
                    content=content,
                    uploader=admin,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"初始化完成：admin / admin123456，测试账号 sales01/design01/prod01/finance01/aftersales01/admin01 / demo123456，"
                f"已准备 {len(orders_data)} 条演示订单"
            )
        )
