from django.core.management.base import BaseCommand
import random

from accounts.models import User, Student
from core.models import SchoolClass
from course.models import Subject


DEFAULT_PASSWORD = "1234"


class Command(BaseCommand):
    help = "Fixed seed script (students, teachers, classes, subjects)"

    def handle(self, *args, **kwargs):

        self.stdout.write("Deleting old data...")

        Student.objects.all().delete()
        SchoolClass.objects.all().delete()
        Subject.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        # =====================================================
        # SUBJECTS (LEVEL BASED)
        # =====================================================
        levels = ["F1", "F2", "F3", "F4", "F5"]

        base_subjects = [
            "Mathematics",
            "English",
            "Physics",
            "Chemistry",
            "Biology",
            "Geography",
            "History",
            "Computer Studies",
        ]

        subjects = []

        for level in levels:
            for name in base_subjects:

                subject = Subject.objects.create(
                    title=f"{name} {level}",
                    code=f"{name[:4].upper()}-{level}",
                    summary=f"{name} for {level} students"
                )
                subjects.append(subject)

        self.stdout.write(self.style.SUCCESS("Subjects created"))

        # =====================================================
        # CLASSES
        # =====================================================
        classes = []

        for level in levels:
            for letter in ["A", "B"]:
                classes.append(
                    SchoolClass.objects.create(
                        name=f"{level}{letter}",
                        level=level
                    )
                )

        self.stdout.write(self.style.SUCCESS("Classes created"))

        # =====================================================
        # TEACHERS (FIXED LOGIN)
        # =====================================================
        teachers = []

        for i in range(1, 6):
            teacher = User.objects.create_user(
                username=f"teacher{i}",
                email=f"teacher{i}@school.com",
                password=DEFAULT_PASSWORD,
                first_name=f"Teacher{i}",
                last_name="User",
                is_lecturer=True,
                is_active=True
            )
            teachers.append(teacher)

            self.stdout.write(f"Teacher created → teacher{i} / {DEFAULT_PASSWORD}")

        # =====================================================
        # STUDENTS (FIXED LOGIN)
        # =====================================================
        students = []
        user = User.objects.create_user(
            username=f"student0",
            email=f"bkhoromeng@gmail.com",
            password=DEFAULT_PASSWORD,
            first_name="Boris",
            last_name="Khoromeng",
            is_student=True,
            gender="M",
            is_active=True

        )
        student = Student.objects.create(
            student=user,
            level="F3",
            student_class=classes[2]
        )
        for i in range(1, 31):

            user = User.objects.create_user(
                username=f"student{i}",
                email=f"student{i}@school.com",
                password=DEFAULT_PASSWORD,
                first_name=f"Student{i}",
                last_name="User",
                is_student=True,
                gender=random.choice(["M", "F"]),
                is_active=True
            )

            student = Student.objects.create(
                student=user,
                level=random.choice(levels),
                student_class=random.choice(classes)
            )

            students.append(student)

            self.stdout.write(f"Student created → student{i} / {DEFAULT_PASSWORD}")

        # =====================================================
        # FINAL SUMMARY
        # =====================================================
        self.stdout.write("\n")
        self.stdout.write(self.style.SUCCESS("=== LOGIN DETAILS ==="))
        self.stdout.write("All passwords: 1234")
        self.stdout.write("Teachers: teacher1 - teacher5")
        self.stdout.write("Students: student1 - student30")