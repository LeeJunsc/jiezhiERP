import re
import zipfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from xml.etree import ElementTree

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from customers.models import Customer
from orders.models import DesignOption, Order, OrderItem
from orders.services import next_order_no, submit_order
from stores.models import Store
from system_settings.models import PaymentChannel


NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


DESIGN_OPTION_MAP = {
    "是": "新订单需要设计",
    "否-仅标注": "仅标注",
    "仅标注": "仅标注",
    "否-续订": "续订无需设计",
    "续订无需设计": "续订无需设计",
    "否": "续订无需设计",
}


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()


def column_index(cell_ref):
    letters = re.sub(r"[^A-Z]", "", cell_ref.upper())
    index = 0
    for char in letters:
        index = index * 26 + ord(char) - ord("A") + 1
    return index - 1


def shared_strings(archive):
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    values = []
    for item in root.findall("x:si", NS):
        texts = [node.text or "" for node in item.findall(".//x:t", NS)]
        values.append("".join(texts))
    return values


def cell_value(cell, strings):
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:t", NS))
    value_node = cell.find("x:v", NS)
    if value_node is None:
        return ""
    value = value_node.text or ""
    if cell_type == "s":
        try:
            return strings[int(value)]
        except (ValueError, IndexError):
            return ""
    return value


def read_xlsx_rows(uploaded_file):
    content = uploaded_file.read()
    rows = []
    with zipfile.ZipFile(BytesIO(content)) as archive:
        strings = shared_strings(archive)
        sheet_names = sorted(name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"))
        for sheet_name in sheet_names:
            root = ElementTree.fromstring(archive.read(sheet_name))
            for row_node in root.findall(".//x:sheetData/x:row", NS):
                values = []
                for cell in row_node.findall("x:c", NS):
                    index = column_index(cell.attrib.get("r", "A1"))
                    while len(values) <= index:
                        values.append("")
                    values[index] = cell_value(cell, strings)
                rows.append(values)
    return rows


def parse_rows(uploaded_file):
    raw_rows = read_xlsx_rows(uploaded_file)
    parsed = []
    for raw in raw_rows:
        if not any(normalize_text(value) for value in raw):
            continue
        headers = [normalize_text(value) for value in raw]
        if "订单号" in headers and "订单金额" in headers:
            current_headers = headers
            continue
        if "current_headers" not in locals():
            continue
        item = {}
        for index, header in enumerate(current_headers):
            if header:
                item[header] = raw[index] if index < len(raw) else ""
        parsed.append(item)
    return parsed


def parse_datetime(value):
    text = normalize_text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            return timezone.make_aware(datetime.strptime(text, fmt))
        except ValueError:
            continue
    return None


def parse_amount(value):
    text = normalize_text(value).replace(",", "")
    if not text:
        return Decimal("0.00")
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0.00")


def platform_for_store(name):
    text = normalize_text(name).lower()
    if "pdd" in text or "多多" in text or "拼多多" in text:
        return Store.Platform.PINDUODUO
    if "tb" in text or "淘宝" in text or "天猫" in text:
        return Store.Platform.TAOBAO
    if "抖音" in text or "douyin" in text:
        return Store.Platform.DOUYIN
    if "小红书" in text:
        return Store.Platform.XIAOHONGSHU
    return Store.Platform.OTHER


def customer_name(value):
    text = normalize_text(value)
    if not text:
        return "历史导入客户"
    return text


def extract_phone(text):
    match = re.search(r"1[3-9]\d{9}", normalize_text(text))
    return match.group(0) if match else ""


def design_option_for(value, actor):
    raw = normalize_text(value)
    name = DESIGN_OPTION_MAP.get(raw, raw or "新订单需要设计")
    requires_design = name != "续订无需设计"
    option, _ = DesignOption.objects.get_or_create(
        name=name,
        defaults={"requires_design": requires_design, "sort_order": 90, "created_by": actor},
    )
    return option


def imported_status(row):
    approval_status = normalize_text(row.get("审批状态"))
    approval_result = normalize_text(row.get("审批结果"))
    if "撤销" in approval_status or "撤销" in approval_result:
        return Order.Status.CANCELLED
    if approval_status == "完成" and (not approval_result or approval_result == "同意"):
        return Order.Status.COMPLETED
    return Order.Status.DRAFT


def build_remark(row):
    parts = []
    for label in ["收货信息", "其它说明", "设计稿/素材", "是否需要跟色", "传统印刷产品价格"]:
        value = normalize_text(row.get(label))
        if value:
            parts.append(f"{label}: {value}")
    return "\n".join(parts)


def import_orders_from_xlsx(uploaded_file, actor, dry_run=False):
    rows = parse_rows(uploaded_file)
    result = {"dry_run": dry_run, "total": len(rows), "created": 0, "skipped": 0, "failed": 0, "details": []}
    platform_channel = PaymentChannel.objects.filter(code="platform").first()
    User = get_user_model()
    salesperson = actor if actor.is_authenticated else User.objects.filter(is_superuser=True).first()

    with transaction.atomic():
        for index, row in enumerate(rows, start=2):
            platform_order_no = normalize_text(row.get("订单号"))
            if not platform_order_no:
                result["failed"] += 1
                result["details"].append({"row": index, "status": "failed", "message": "缺少订单号"})
                continue

            if Order.objects.filter(platform_order_no=platform_order_no).exclude(status=Order.Status.CANCELLED).exists():
                result["skipped"] += 1
                result["details"].append({"row": index, "status": "skipped", "message": f"平台订单号已存在：{platform_order_no}"})
                continue

            try:
                with transaction.atomic():
                    store_name = normalize_text(row.get("来源店铺")) or "历史导入店铺"
                    store_platform = platform_for_store(store_name)
                    store, _ = Store.objects.get_or_create(
                        name=store_name,
                        defaults={
                            "platform": store_platform,
                            "custom_platform": store_name if store_platform == Store.Platform.OTHER else "",
                            "owner": salesperson,
                            "created_by": actor,
                        },
                    )
                    shipping_info = normalize_text(row.get("收货信息"))
                    customer, _ = Customer.objects.get_or_create(
                        name=customer_name(row.get("客户id")),
                        defaults={
                            "source": store_name,
                            "phone": extract_phone(shipping_info),
                            "address": shipping_info,
                            "created_by": actor,
                        },
                    )
                    amount = parse_amount(row.get("订单金额"))
                    status = imported_status(row)
                    started_at = parse_datetime(row.get("发起时间"))
                    completed_at = parse_datetime(row.get("完成时间")) if status == Order.Status.COMPLETED else None
                    order = Order.objects.create(
                        order_no=next_order_no(),
                        platform_order_no=platform_order_no,
                        store=store,
                        customer=customer,
                        salesperson=salesperson,
                        design_option=design_option_for(row.get("是否需要设计"), actor),
                        status=Order.Status.DRAFT,
                        total_amount=amount,
                        paid_amount=amount,
                        payment_status=Order.PaymentStatus.PAID,
                        payment_channel=platform_channel,
                        customization_note=normalize_text(row.get("订单说明")),
                        remark=build_remark(row),
                        submitted_at=started_at,
                        completed_at=completed_at,
                        created_by=actor,
                    )
                    OrderItem.objects.create(
                        order=order,
                        product_name=normalize_text(row.get("产品类别")) or normalize_text(row.get("订单说明")) or "历史导入产品",
                        quantity=1,
                        unit_price=amount,
                        line_amount=amount,
                        custom_note=normalize_text(row.get("订单说明")),
                        created_by=actor,
                    )
                    if status == Order.Status.CANCELLED:
                        order.status = Order.Status.CANCELLED
                        order.save(update_fields=["status", "updated_at"])
                    elif status == Order.Status.COMPLETED:
                        order.status = Order.Status.COMPLETED
                        order.save(update_fields=["status", "submitted_at", "completed_at", "updated_at"])
                    else:
                        submit_order(order, actor)
                    result["created"] += 1
                    result["details"].append({"row": index, "status": "created", "message": order.order_no})
            except Exception as exc:
                result["failed"] += 1
                result["details"].append({"row": index, "status": "failed", "message": str(exc)})

        if dry_run:
            transaction.set_rollback(True)

    return result
