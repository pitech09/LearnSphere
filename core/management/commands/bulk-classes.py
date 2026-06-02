"""
Bulk import school classes from a CSV file.

Usage:
    python manage.py bulk-classes <school_subdomain> <csv_file>

CSV Format (header required):

    name,level
    ─────────────────────────────────────────────
    name   - Class name (e.g. "Form 1A", "Form 2B", "Science Lab")
    level  - Form level: F1, F2, F3, F4, F5, or F6

Example CSV:

    name,level
    Form 1A,F1
    Form 1B,F1
    Form 2A,F2
    Form 2B,F2
    Form 3A,F3
    Form 3B,F3
    Form 4A,F4
    Form 4B,F4
    Form 5A,F5
    Form 5B,F5

Run:
    python manage.py bulk-classes green-valley classes.csv

You can also use the built-in sample:
    python manage.py bulk-classes green-valley media/seed/classes_sample.csv
"""

import csv
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import School, SchoolClass


VALID_LEVELS = {"F1", "F2", "F3", "F4", "F5", "F6"}


class Command(BaseCommand):

    help = "Bulk import school classes from a CSV file"

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
        self.stdout.write(self.style.SUCCESS(f"📦 Importing classes into {school.name}"))
        self.stdout.write("")

        # ── Validate file ───────────────────────────────────
        if not os.path.exists(csv_path):
            raise CommandError(f'File not found: {csv_path}')

        created = 0
        skipped = 0
        errors = []

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Validate required headers
            required = {"name", "level"}
            missing = required - {h.strip() for h in reader.fieldnames}
            if missing:
                raise CommandError(
                    f"CSV is missing required column(s): {', '.join(sorted(missing))}"
                )

            for line_num, row in enumerate(reader, start=2):
                name = row.get("name", "").strip()
                level = row.get("level", "").strip().upper()

                if not name:
                    errors.append(f"Line {line_num}: Missing class name. Skipping.")
                    skipped += 1
                    continue

                if level not in VALID_LEVELS:
                    errors.append(
                        f"Line {line_num}: '{level}' is not a valid level "
                        f"(use F1, F2, F3, F4, F5, F6). Skipping."
                    )
                    skipped += 1
                    continue

                # Check for duplicate class name in this school
                if SchoolClass.objects.filter(school=school, name__iexact=name).exists():
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠  Class '{name}' already exists. Skipping.")
                    )
                    skipped += 1
                    continue

                try:
                    SchoolClass.objects.create(
                        school=school,
                        name=name,
                        level=level,
                    )
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✅ {name} (Level {level})"))
                except Exception as e:
                    errors.append(f"Line {line_num}: Failed to create class '{name}' — {e}")
                    skipped += 1

        # ── Summary ─────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"🎉 Successfully created {created} class(es)"))
        if skipped:
            self.stdout.write(self.style.WARNING(f"⚠  Skipped {skipped} row(s)"))
        if errors:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR("Errors:"))
            for err in errors:
                self.stdout.write(self.style.ERROR(f"  • {err}"))

        self.stdout.write("")
        self.stdout.write("─" * 50)
        self.stdout.write("DESIRED CSV FORMAT:")
        self.stdout.write("")
        self.stdout.write("name,level")
        self.stdout.write("Form 1A,F1")