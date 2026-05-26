from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_alter_schoolclass_unique_together_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="session",
            name="session",
            field=models.CharField(max_length=200),
        ),
    ]
