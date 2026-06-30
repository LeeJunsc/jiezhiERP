from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0003_alter_invoicerequest_invoice_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoicerequest",
            name="approval_remark",
            field=models.TextField(blank=True),
        ),
    ]
