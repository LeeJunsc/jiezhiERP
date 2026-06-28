from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from audit.services import write_log
from design.models import DesignTask
from orders.models import Order
from orders.numbering import build_number
from production.models import ProductionArrangement


def next_order_no():
    return build_number("JZ", Order, "order_no")


def next_design_task_no():
    return build_number("JZD", DesignTask, "task_no")


def next_production_arrangement_no():
    return build_number("JZP", ProductionArrangement, "arrangement_no")


@transaction.atomic
def submit_order(order, actor):
    if order.status != Order.Status.DRAFT:
        raise ValidationError("只有草稿订单可以提交。")

    before = {"status": order.status}
    order.status = Order.Status.SUBMITTED
    order.submitted_at = timezone.now()
    order.save(update_fields=["status", "submitted_at", "updated_at"])

    if order.design_option.requires_design:
        DesignTask.objects.create(
            task_no=next_design_task_no(),
            order=order,
            status=DesignTask.Status.PENDING,
            created_by=actor,
        )
        order.status = Order.Status.PENDING_DESIGN
        order.save(update_fields=["status", "updated_at"])
        action = "submit_and_create_design_task"
    else:
        ProductionArrangement.objects.create(
            arrangement_no=next_production_arrangement_no(),
            order=order,
            status=ProductionArrangement.Status.PENDING,
            created_by=actor,
        )
        order.status = Order.Status.PENDING_PRODUCTION
        order.save(update_fields=["status", "updated_at"])
        action = "submit_and_create_production_arrangement"

    write_log(actor, order, action, before=before, after={"status": order.status})
    return order


@transaction.atomic
def cancel_order(order, actor):
    if order.status in [Order.Status.COMPLETED, Order.Status.CANCELLED]:
        raise ValidationError("已完成或已取消订单不能取消。")

    before = {"status": order.status}
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    write_log(actor, order, "cancel_order", before=before, after={"status": order.status})
    return order
