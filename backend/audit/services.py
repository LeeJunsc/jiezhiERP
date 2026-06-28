from audit.models import OperationLog


def write_log(actor, business, action, before=None, after=None, remark=""):
    if not actor or not actor.is_authenticated:
        return None
    return OperationLog.objects.create(
        actor=actor,
        business_type=business.__class__.__name__,
        business_id=business.id,
        action=action,
        before_value=before,
        after_value=after,
        remark=remark,
        created_by=actor,
    )
