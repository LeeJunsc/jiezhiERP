from django.utils import timezone


def build_number(prefix, model, field_name):
    today = timezone.localdate().strftime("%Y%m%d")
    starts_with = f"{prefix}{today}"
    count = model.objects.filter(**{f"{field_name}__startswith": starts_with}).count() + 1
    return f"{starts_with}{count:04d}"
