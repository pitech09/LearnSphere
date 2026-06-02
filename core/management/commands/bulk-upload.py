"""
Bulk import students from a CSV or text file.

Usage:
    python manage.py bulk-upload <school_subdomain> <csv_file>

Desired CSV format:
    The CSV file MUST have a header row with the following column names:

    first_name,last_name,gender,class_name,class_level,phone,email,address

    ─ Required columns:
        first_name   - Student's first name
        last_name    - Student's last name
        gender       - "M" (Male) or "F" (Female)
        class_name   - The exact name of the SchoolClass (e.g. "Form 1A", "Science")
                       This class must already exist in the school.
        class_level  - "F1", "F2", "F3", "F4", or "F5"

    ─ Optional columns (leave blank if unknown):
        phone        - Student's phone number
        email        - Student's email address
        address      - Student's physical address

    ─ Parent columns (all optional, prefix with parent_):
        parent_first_name
        parent_last_name
        parent_phone
        parent_email
        parent_relation    - e.g. "Father", "Mother", "Guardian"

    Example row:
        first_name,last_name,gender,class_name,class_level,phone,email,address,parent_first_name,parent_last_name,parent_phone,parent_email,parent_relation
        John,Doe,M,Form 1A,F1,+26650001234,john@example.com,Maseru,Jane,Doe,+26651234567,jane@example.com,Mother

    Run from project root:
        python manage.py bulk-upload green-valley students.csv
"""

import csv
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import Parent, Student, User
from accounts.utils import send_new_account_sms
from core.models import School, SchoolClass

GENDERS = {"M": "Male", "F": "Female"}


DEFAULT_PASSWORD = "Student123!"
HASHED_PASSWORD = make_password(DEFAULT_PASSWORD)


class Command(BaseCommand):

    help = "Bulk import students from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("school_subdomain", type=str, help="School subdomain (slug)")
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")

    @transaction.atomic
    def handle(self, *args, **options):
        school_subdomain = options["school_subdomain"]
        csv_path = options["csv_file"]

        # ── Resolve School ──────────────────────────────────
        try:
            school = School.objects.get(subdomain=school_subdomain)
        except School.DoesNotExist:
            raise CommandError(f'School with subdomain "{school_subdomain}" not found.')

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"📥 Importing students into {school.name}"))
        self.stdout.write("")

        # ── Validate file ───────────────────────────────────
        if not os.path.exists(csv_path):
            raise CommandError(f'File not found: {csv_path}')

        imported = 0
        skipped = 0
        errors = []

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Validate required headers
            required = {"first_name", "last_name", "gender", "class_name", "class_level"}
            missing = required - {h.strip() for h in reader.fieldnames}
            if missing:
                raise CommandError(
                    f"CSV is missing required column(s): {', '.join(sorted(missing))}"
                )

            for line_num, row in enumerate(reader, start=2):
                first_name = row.get("first_name", "").strip()
                last_name = row.get("last_name", "").strip()
                gender_raw = row.get("gender", "").strip().upper()
                class_name = row.get("class_name", "").strip()
                class_level = row.get("class_level", "").strip().upper()
                phone = row.get("phone", "").strip()
                email = row.get("email", "").strip()
                address = row.get("address", "").strip()

                parent_fn = row.get("parent_first_name", "").strip()
                parent_ln = row.get("parent_last_name", "").strip()
                parent_phone = row.get("parent_phone", "").strip()
                parent_email = row.get("parent_email", "").strip()
                parent_relation = row.get("parent_relation", "Guardian").strip()

                # ── Validate gender ──────────────────────────
                gender = gender_raw if gender_raw in ("M", "F") else None

                # ── Resolve SchoolClass ─────────────────────
                try:
                    school_class = SchoolClass.objects.get(school=school, name=class_name)
                except SchoolClass.DoesNotExist:
                    errors.append(
                        f"Line {line_num}: Class '{class_name}' not found for school. Skipping."
                    )
                    skipped += 1
                    continue

                # ── Auto-generate username ──────────────────
                base_username = f"{first_name}.{last_name}".lower()
                base_username = "".join(c for c in base_username if c.isalnum() or c in "._-")
                if not base_username:
                    import uuid
                    base_username = f"student{uuid.uuid4().hex[:8]}"

                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                # ── Create User ─────────────────────────────
                try:
                    user = User.objects.create(
                        username=username,
                        school=school,
                        first_name=first_name,
                        last_name=last_name,
                        gender=gender,
                        phone=phone or None,
                        email=email or None,
                        address=address or None,
                        is_student=True,
                        is_active=True,
                        password=HASHED_PASSWORD,
                    )
                except Exception as e:
                    errors.append(f"Line {line_num}: Failed to create user {first_name} {last_name} — {e}")
                    skipped += 1
                    continue

                # ── Create Student ──────────────────────────
                try:
                    Student.objects.create(
                        student=user,
                        level=class_level,
                        student_class=school_class,
                    )
                except Exception as e:
                    # Roll back the user if student creation fails
                    user.delete()
                    errors.append(f"Line {line_num}: Failed to create student record for {first_name} {last_name} — {e}")
                    skipped += 1
                    continue

                # ── Create Parent (optional) ────────────────
                if parent_fn and parent_ln:
                    parent_username = f"parent.{username}"
                    try:
                        parent_user, _ = User.objects.get_or_create(
                            username=parent_username,
                            defaults=dict(
                                school=school,
                                first_name=parent_fn,
                                last_name=parent_ln,
                                phone=parent_phone or None,
                                email=parent_email or None,
                                is_parent=True,
                                is_active=True,
                                password=HASHED_PASSWORD,
                            ),
                        )
                        Parent.objects.get_or_create(
                            user=parent_user,
                            defaults=dict(
                                student=Student.objects.get(student=user),
                                first_name=parent_fn,
                                last_name=parent_ln,
                                phone=parent_phone or None,
                                email=parent_email or None,
                                relation_ship=parent_relation,
                            ),
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠  Could not create parent for {first_name} {last_name}: {e}"
                            )
                        )

                imported += 1
                self.stdout.write(self.style.SUCCESS(f"  ✅ {first_name} {last_name} ({username})"))

        # ── Summary ─────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"🎉 Successfully imported {imported} student(s)"))
        if skipped:
            self.stdout.write(self.style.WARNING(f"⚠  Skipped {skipped} row(s)"))
        if errors:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR("Errors:"))
            for err in errors:
                self.stdout.write(self.style.ERROR(f"  • {err}"))

        self.stdout.write("")
        self.stdout.write(self.style.WARNING(f"🔑 Default password for all students: {DEFAULT_PASSWORD}"))
        self.stdout.write("")
        self.stdout.write("─" * 50)
        self.stdout.write("DESIRED CSV FORMAT:")
        self.stdout.write("")
        self.stdout.write(
            "first_name,last_name,gender,class_name,class_level,"
            "phone,email,address,"
            "parent_first_name,parent_last_name,parent_phone,parent_email,parent_relation"
        )
        self.stdout.write(
            "John,Doe,M,Form 1A,F1,+26650001234,john@example.com,Maseru,"
            "Jane,Doe,+26651234567,jane@example.com,Mother"
        )
        self.stdout.write("")