# Generated manually to add the Income ledger model.

from django.conf import settings
from django.db import migrations, models
from django.db.models import deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0024_school_registration_number_school_trial_ends_on"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Income",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(max_length=200)),
                ("category", models.CharField(choices=[("fees", "School Fees"), ("donations", "Donations"), ("grants", "Grants"), ("sales", "Sales"), ("transport", "Transport"), ("events", "Events & Activities"), ("other", "Other Income")], default="other", max_length=30)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("income_date", models.DateField(default=django.utils.timezone.localdate)),
                ("reference", models.CharField(blank=True, max_length=120)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("recorded_by", models.ForeignKey(blank=True, null=True, on_delete=deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("school", models.ForeignKey(on_delete=deletion.CASCADE, related_name="incomes", to="core.school")),
            ],
            options={
                "ordering": ("-income_date", "-created_at"),
            },
        ),
        migrations.AddIndex(
            model_name="income",
            index=models.Index(fields=["school", "-income_date"], name="income_school_date_idx"),
        ),
        migrations.AddIndex(
            model_name="income",
            index=models.Index(fields=["school", "category"], name="income_school_category_idx"),
        ),
    ]
