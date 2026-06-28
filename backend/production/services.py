from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from audit.services import write_log
from orders.models import Order
from production.models import ProductionArrangement


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
