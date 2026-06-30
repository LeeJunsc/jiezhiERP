from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("after_sales", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="aftersalesrequest",
            name="remark",
            field=models.TextField(blank=True),
        ),
    ]
