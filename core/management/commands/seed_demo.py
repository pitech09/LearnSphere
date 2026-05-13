import random
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from accounts.models import Student
from core.models import SchoolClass
from course.models import Subject
from core.utils import send_html_email

User = get_user_model()
DEFAULT_PASSWORD = "1234"

def dummy_send(*args, **kwargs):
    pass

class Command(BaseCommand):
    help = "Seed students and teachers with proper prefixed IDs"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # Temporarily disable email sending
        original_send = send_html_email
        import core.utils
        core.utils.send_html_email = dummy_send

        # Clear old data
        User.objects.exclude(is_superuser=True).delete()
        Student.objects.all().delete()

        # Create classes
        levels = ["F1","F2","F3","F4","F5"]
        classes = []
        for level in levels:
            for letter in ["A","B"]:
                cls, _ = SchoolClass.objects.get_or_create(name=f"{level}{letter}", level=level)
                classes.append(cls)

        # Create subjects
        base_subjects = ["Mathematics","English","Physics","Chemistry","Biology","Geography","History","Computer Studies"]
        for level in levels:
            for name in base_subjects:
                Subject.objects.get_or_create(
                    title=f"{name} {level}",
                    defaults={'code': f"{name[:4].upper()}-{level}", 'summary': f"{name} for {level} students"}
                )

        current_year = datetime.now().strftime("%Y")

        # ----- TEACHERS (lecturers) -----
        lecturers_count = 0
        for i in range(1, 6):
            lecturers_count += 1
            lecturer_id = f"{settings.LECTURER_ID_PREFIX}-{current_year}-{lecturers_count}"
            teacher = User.objects.create_user(
                username=lecturer_id,
                email=f"teacher{i}@school.com",
                password=DEFAULT_PASSWORD,
                first_name=f"Teacher{i}",
                last_name="User",
                is_lecturer=True,
                is_active=True
            )
            self.stdout.write(f"Teacher: {lecturer_id} / {DEFAULT_PASSWORD}")

        # ----- STUDENTS -----
        students_count = 0
        for i in range(1, 31):
            students_count += 1
            student_id = f"{settings.STUDENT_ID_PREFIX}-{current_year}-{students_count}"
            user = User.objects.create_user(
                username=student_id,
                email=f"student{i}@school.com",
                password=DEFAULT_PASSWORD,
                first_name=f"Student{i}",
                last_name="User",
                is_student=True,
                gender=random.choice(["M","F"]),
                is_active=True
            )
            Student.objects.create(
                student=user,
                level=random.choice(levels),
                student_class=random.choice(classes)
            )
            self.stdout.write(f"Student: {student_id} / {DEFAULT_PASSWORD}")

        # ----- SUPERUSER -----
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@school.com",
                password=DEFAULT_PASSWORD,
                first_name="Admin",
                last_name="User"
            )
            self.stdout.write("Admin: admin / 1234")

        # Test authentication
        self.stdout.write("\n--- Testing login with prefixed IDs ---")
        test_ids = [
            f"{settings.LECTURER_ID_PREFIX}-{current_year}-1",
            f"{settings.STUDENT_ID_PREFIX}-{current_year}-1",
            "admin"
        ]
        for uid in test_ids:
            from django.contrib.auth import authenticate
            user = authenticate(username=uid, password=DEFAULT_PASSWORD)
            if user:
                self.stdout.write(self.style.SUCCESS(f"✅ {uid} authenticated"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ {uid} authentication failed"))

        # Restore email sending
        core.utils.send_html_email = original_send