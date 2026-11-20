from django.db import migrations, models
from django.db.models import Q
from django.db.models.functions import Lower


def normalize_and_clear_duplicates(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    users = User.objects.all().order_by("id")

    # Normalize values before the constraints are created. Prefer an admin,
    # then staff, then the oldest account when legacy data conflicts.
    for user in users:
        updates = []
        if user.email:
            email = user.email.strip().lower()
            if email != user.email:
                user.email = email
                updates.append("email")
        elif user.email == "":
            user.email = None
            updates.append("email")

        if user.phone:
            import re
            phone = re.sub(r"[\s().-]+", "", user.phone.strip())
            if phone != user.phone:
                user.phone = phone
                updates.append("phone")
        elif user.phone == "":
            user.phone = None
            updates.append("phone")

        if updates:
            user.save(update_fields=updates)

    for field in ("email", "phone"):
        seen = set()
        duplicate_users = User.objects.exclude(**{f"{field}__isnull": True}).exclude(
            **{field: ""}
        ).order_by("id")
        duplicate_users = sorted(
            duplicate_users,
            key=lambda user: (
                0 if user.is_superuser else 1,
                0 if user.is_staff else 1,
                user.id,
            ),
        )
        for user in duplicate_users:
            value = getattr(user, field)
            key = value.casefold() if field == "email" else value
            if key in seen:
                setattr(user, field, None)
                user.save(update_fields=[field])
            else:
                seen.add(key)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0009_alter_parent_user"),
    ]

    operations = [
        migrations.RunPython(
            normalize_and_clear_duplicates,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                Lower("email"),
                condition=Q(email__isnull=False) & ~Q(email=""),
                name="acct_user_unique_email_ci",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                fields=("phone",),
                condition=Q(phone__isnull=False) & ~Q(phone=""),
                name="acct_user_unique_phone",
            ),
        ),
    ]
