from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("after_sales", "0002_aftersalesrequest_remark"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aftersalesrequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "待处理"),
                    ("processing", "处理中"),
                    ("completed", "已完成"),
                    ("closed", "已驳回"),
                ],
                default="pending",
                max_length=30,
            ),
        ),
    ]
