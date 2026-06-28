from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from audit.services import write_log
from design.models import DesignTask
from orders.models import Order
from orders.services import next_production_arrangement_no
from production.models import ProductionArrangement


@transaction.atomic
def claim_design_task(task, actor):
    if task.status not in [DesignTask.Status.PENDING, DesignTask.Status.NEEDS_CHANGES]:
        raise ValidationError("当前设计任务不能领取。")
    before = {"status": task.status, "designer_id": str(task.designer_id) if task.designer_id else None}
    task.designer = actor
    task.status = DesignTask.Status.DESIGNING
    task.save(update_fields=["designer", "status", "updated_at"])

    order = task.order
    order.status = Order.Status.DESIGNING
    order.save(update_fields=["status", "updated_at"])

    write_log(actor, task, "claim_design_task", before=before, after={"status": task.status})
    return task


@transaction.atomic
def confirm_design_task(task, actor):
    if task.status not in [
        DesignTask.Status.DESIGNING,
        DesignTask.Status.WAITING_CONFIRMATION,
        DesignTask.Status.NEEDS_CHANGES,
    ]:
        raise ValidationError("当前设计任务不能确认。")

    before = {"status": task.status}
    task.status = DesignTask.Status.CONFIRMED
    task.confirmed_at = timezone.now()
    task.save(update_fields=["status", "confirmed_at", "updated_at"])

    order = task.order
    ProductionArrangement.objects.get_or_create(
        order=order,
        defaults={
            "arrangement_no": next_production_arrangement_no(),
            "status": ProductionArrangement.Status.PENDING,
            "created_by": actor,
        },
    )
    order.status = Order.Status.PENDING_PRODUCTION
    order.save(update_fields=["status", "updated_at"])

    write_log(actor, task, "confirm_design_task", before=before, after={"status": task.status})
    write_log(actor, order, "design_confirmed_to_production", after={"status": order.status})
    return task
