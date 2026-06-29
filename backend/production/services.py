from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from audit.services import write_log
from design.models import DesignTask
from orders.models import Order
from orders.numbering import build_number
from production.models import ProductionArrangement


def next_design_task_no():
    return build_number("JZD", DesignTask, "task_no")


@transaction.atomic
def schedule_arrangement(arrangement, actor, factory_name="", planned_finish_at=None, remark=""):
    if arrangement.status in [ProductionArrangement.Status.CONFIRMED]:
        raise ValidationError("已确认的生产安排不能再次修改。")
    before = {"status": arrangement.status}
    arrangement.factory_name = factory_name or arrangement.factory_name
    arrangement.planned_finish_at = planned_finish_at or arrangement.planned_finish_at
    arrangement.remark = remark or arrangement.remark
    arrangement.owner = actor
    arrangement.status = ProductionArrangement.Status.SCHEDULED
    arrangement.save(update_fields=["factory_name", "planned_finish_at", "remark", "owner", "status", "updated_at"])
    write_log(actor, arrangement, "schedule_production_arrangement", before=before, after={"status": arrangement.status})
    return arrangement


@transaction.atomic
def confirm_arrangement(arrangement, actor):
    if arrangement.status not in [ProductionArrangement.Status.PENDING, ProductionArrangement.Status.SCHEDULED]:
        raise ValidationError("当前生产安排不能确认。")
    before = {"status": arrangement.status}
    arrangement.owner = arrangement.owner or actor
    arrangement.status = ProductionArrangement.Status.CONFIRMED
    arrangement.confirmed_at = timezone.now()
    arrangement.save(update_fields=["owner", "status", "confirmed_at", "updated_at"])

    order = arrangement.order
    order.status = Order.Status.COMPLETED
    order.completed_at = timezone.now()
    order.save(update_fields=["status", "completed_at", "updated_at"])

    write_log(actor, arrangement, "confirm_production_arrangement", before=before, after={"status": arrangement.status})
    write_log(actor, order, "order_completed", after={"status": order.status})
    return arrangement


@transaction.atomic
def return_arrangement_to_design(arrangement, actor, remark=""):
    if arrangement.status == ProductionArrangement.Status.CONFIRMED:
        raise ValidationError("已完成订单不能退回设计。")

    before = {"status": arrangement.status}
    arrangement.owner = arrangement.owner or actor
    arrangement.status = ProductionArrangement.Status.EXCEPTION
    arrangement.remark = remark or arrangement.remark
    arrangement.save(update_fields=["owner", "status", "remark", "updated_at"])

    order = arrangement.order
    task, created = DesignTask.objects.get_or_create(
        order=order,
        defaults={
            "task_no": next_design_task_no(),
            "status": DesignTask.Status.PENDING,
            "remark": remark,
            "created_by": actor,
        },
    )
    if not created:
        task.status = DesignTask.Status.NEEDS_CHANGES
        task.remark = remark or task.remark
        task.save(update_fields=["status", "remark", "updated_at"])

    order.status = Order.Status.PENDING_DESIGN
    order.save(update_fields=["status", "updated_at"])

    write_log(actor, arrangement, "return_production_to_design", before=before, after={"status": arrangement.status})
    write_log(actor, order, "returned_to_design", after={"status": order.status})
    return arrangement


@transaction.atomic
def reject_arrangement_order(arrangement, actor, remark=""):
    if arrangement.status == ProductionArrangement.Status.CONFIRMED:
        raise ValidationError("已完成订单不能驳回。")

    before = {"status": arrangement.status}
    arrangement.owner = arrangement.owner or actor
    arrangement.status = ProductionArrangement.Status.EXCEPTION
    arrangement.remark = remark or arrangement.remark
    arrangement.save(update_fields=["owner", "status", "remark", "updated_at"])

    order = arrangement.order
    order_before = {"status": order.status}
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])

    write_log(actor, arrangement, "reject_production_arrangement", before=before, after={"status": arrangement.status})
    write_log(actor, order, "reject_order_from_production", before=order_before, after={"status": order.status})
    return arrangement
