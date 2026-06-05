# Generated manually to restore legacy school fields referenced by the app.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_sync_current_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="school",
            name="registration_number",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="school",
            name="trial_ends_on",
            field=models.DateField(blank=True, null=True),
        ),
    ]
