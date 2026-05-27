from datetime import timedelta
from decimal import Decimal
import csv
import os
import random

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from accounts.models import Parent, Student, User
from core.models import (
    FEE_STATUS_PARTIAL,
    FeePayment,
    School,
    SchoolClass,
    SchoolFee,
    Session,
    Term,
)
from course.models import Subject
from result.models import TakenCourse


fake = Faker()

# =========================================================
# CONFIG
# =========================================================

STUDENTS_PER_CLASS = 15
TEACHERS_PER_SCHOOL = 10

DEFAULT_PASSWORDS = {
    "platform_owner": "PlatformOwner123!",
    "school_admin": "SchoolAdmin123!",
    "teacher": "Teacher123!",
    "student": "Student123!",
    "parent": "Parent123!",
}

HASHED_PASSWORDS = {
    role: make_password(password)
    for role, password in DEFAULT_PASSWORDS.items()
}

LEVEL_SUBJECTS = {
    "F1": [
        ("Mathematics", "MATH"),
        ("English", "ENG"),
        ("Science", "SCI"),
        ("Geography", "GEO"),
        ("Life Skills", "LS"),
    ],
    "F2": [
        ("Mathematics", "MATH"),
        ("English", "ENG"),
        ("Science", "SCI"),
        ("History", "HIS"),
        ("Computer Studies", "CS"),
    ],
    "F3": [
        ("Mathematics", "MATH"),
        ("English", "ENG"),
        ("Science", "SCI"),
        ("History", "HIS"),
        ("Computer Studies", "CS"),
    ],
    "F4": [
        ("Mathematics", "MATH"),
        ("English", "ENG"),
        ("Computer Studies", "CS"),
        ("Geography", "GEO"),
    ],
    "F5": [
        ("Mathematics", "MATH"),
        ("English", "ENG"),
        ("Computer Studies", "CS"),
        ("History", "HIS"),
    ],
}

PLATFORM_OWNER = (
    "platform_owner",
    "PlatformOwner123!",
    "Platform",
    "Owner",
)

SCHOOLS = [
    {
        "name": "Green Valley High School",
        "subdomain": "green-valley",
    },
    {
        "name": "Blue Mountain Academy",
        "subdomain": "blue-mountain",
    },
]


# =========================================================
# COMMAND
# =========================================================

class Command(BaseCommand):

    help = "LearnSphere LMS Advanced Stress Seeder"

    @transaction.atomic
    def handle(self, *args, **options):

        self.credentials = []

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "🚀 STARTING LEARNSPHERE ADVANCED SEED..."
            )
        )

        self.create_platform_owner()

        for school_data in SCHOOLS:
            self.seed_school(school_data)

        self.print_credentials()
        self.save_credentials_to_file()

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "✅ SEEDING COMPLETE"
            )
        )

    # =========================================================
    # SCHOOL SEED
    # =========================================================

    def seed_school(self, data):

        school = self.create_school(data)

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                f"🏫 Seeding {school.name}"
            )
        )

        school_admin = self.create_school_admin(school)

        teachers = self.create_teachers(school)

        classes = self.create_classes(
            school=school,
            teachers=teachers,
        )

        subjects_by_class = self.create_subjects(
            school=school,
            classes=classes,
            teachers=teachers,
        )

        students = self.create_students(
            school=school,
            classes=classes,
        )

        self.assign_subjects_to_students(
            students=students,
            subjects_by_class=subjects_by_class,
            school=school,
        )

        self.create_parents(
            school=school,
            students=students,
        )

        session = self.create_session(school)

        term = self.create_term(
            school=school,
            session=session,
        )

        self.create_fees(
            school=school,
            students=students,
            session=session,
            term=term,
        )

    # =========================================================
    # SCHOOL
    # =========================================================

    def create_school(self, data):

        school, _ = School.objects.update_or_create(
            subdomain=data["subdomain"],
            defaults={
                "name": data["name"],
                "email": f"admin@{data['subdomain']}.learnsphere.test",
                "phone": "+26650000000",
                "address": "Maseru",
                "status": "active",
                "plan": "growth",
                "subscription_amount": Decimal("750.00"),
                "last_payment_on": timezone.localdate(),
                "next_payment_due_on": timezone.localdate() + timedelta(days=30),
                "trial_ends_on": timezone.localdate() + timedelta(days=7),
                "is_active": True,
                "current_quarter": "Q1",
            },
        )

        return school

    # =========================================================
    # PLATFORM OWNER
    # =========================================================

    def create_platform_owner(self):

        username, password, first, last = PLATFORM_OWNER

        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "school": None,
                "first_name": first,
                "last_name": last,
                "email": "owner@learnsphere.test",
                "phone": "+26650000000",
                "is_superuser": True,
                "is_staff": True,
                "is_active": True,
                "password": HASHED_PASSWORDS["platform_owner"],
            },
        )

        self.credentials.append(
            ("Platform", "Owner", username, password)
        )

    # =========================================================
    # SCHOOL ADMIN
    # =========================================================

    def create_school_admin(self, school):

        username = f"{school.subdomain}_admin"
        password = DEFAULT_PASSWORDS["school_admin"]

        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "school": school,
                "first_name": "School",
                "last_name": "Admin",
                "email": f"{username}@test.com",
                "phone": "+26650000000",
                "is_staff": True,
                "is_active": True,
                "password": HASHED_PASSWORDS["school_admin"],
            },
        )

        self.credentials.append(
            (school.name, "School Admin", username, password)
        )

        return user

    # =========================================================
    # TEACHERS
    # =========================================================

    def create_teachers(self, school):

        teachers = []

        for i in range(TEACHERS_PER_SCHOOL):

            username = f"{school.subdomain}_teacher_{i}"

            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "school": school,
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "email": f"{username}@test.com",
                    "phone": "+26650000000",
                    "is_staff": True,
                    "is_lecturer": True,
                    "is_active": True,
                    "password": HASHED_PASSWORDS["teacher"],
                },
            )

            teachers.append(user)

            self.credentials.append(
                (
                    school.name,
                    "Teacher",
                    username,
                    DEFAULT_PASSWORDS["teacher"],
                )
            )

        return teachers

    # =========================================================
    # CLASSES
    # =========================================================

    def create_classes(self, school, teachers):

        levels = ["F1", "F2", "F3", "F4", "F5"]
        streams = ["A", "B"]

        classes = []

        teacher_index = 0

        for level in levels:
            for stream in streams:

                teacher = teachers[
                    teacher_index % len(teachers)
                ]

                teacher_index += 1

                school_class, _ = SchoolClass.objects.update_or_create(
                    school=school,
                    level=level,
                    name=f"{level}{stream}",
                    defaults={
                        "class_teacher": teacher,
                        "is_active": True,
                    },
                )

                classes.append(school_class)

        return classes

    # =========================================================
    # SUBJECTS
    # =========================================================

    def create_subjects(
        self,
        school,
        classes,
        teachers,
    ):

        subjects_by_class = {}

        for school_class in classes:

            level_subjects = LEVEL_SUBJECTS.get(
                school_class.level,
                [],
            )

            class_subjects = []

            for title, code in level_subjects:

                teacher = random.choice(teachers)

                subject, _ = Subject.objects.update_or_create(
                    school=school,
                    code=f"{school_class.name}-{code}",
                    defaults={
                        "title": title,
                        "teacher": teacher,
                        "school_class": school_class,
                    },
                )

                class_subjects.append(subject)

            subjects_by_class[school_class.id] = class_subjects

        return subjects_by_class

    # =========================================================
    # STUDENTS
    # =========================================================

    def create_students(self, school, classes):

        students = []

        for school_class in classes:

            for i in range(STUDENTS_PER_CLASS):

                username = (
                    f"{school.subdomain}_"
                    f"{school_class.name.lower()}_"
                    f"student_{i}"
                )

                user, _ = User.objects.update_or_create(
                    username=username,
                    defaults={
                        "school": school,
                        "first_name": fake.first_name(),
                        "last_name": fake.last_name(),
                        "email": f"{username}@test.com",
                        "phone": "+26650000000",
                        "is_student": True,
                        "is_active": True,
                        "password": HASHED_PASSWORDS["student"],
                    },
                )

                student, _ = Student.objects.update_or_create(
                    student=user,
                    defaults={
                        "level": school_class.level,
                        "student_class": school_class,
                    },
                )

                students.append(student)

                self.credentials.append(
                    (
                        school.name,
                        "Student",
                        username,
                        DEFAULT_PASSWORDS["student"],
                    )
                )

        return students

    # =========================================================
    # SUBJECT ASSIGNMENT
    # =========================================================

    def assign_subjects_to_students(
        self,
        students,
        subjects_by_class,
        school,
    ):

        bulk = []

        for student in students:

            student_class = student.student_class

            class_subjects = subjects_by_class.get(
                student_class.id,
                [],
            )

            for subject in class_subjects:

                bulk.append(
                    TakenCourse(
                        school=school,
                        student=student,
                        course=subject,
                        quarter="Q1",
                    )
                )

        TakenCourse.objects.bulk_create(
            bulk,
            batch_size=500,
            ignore_conflicts=True,
        )

    # =========================================================
    # PARENTS
    # =========================================================

    def create_parents(self, school, students):

        for i, student in enumerate(students):

            username = f"{school.subdomain}_parent_{i}"

            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "school": school,
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "email": f"{username}@test.com",
                    "phone": "+26650000000",
                    "is_parent": True,
                    "is_active": True,
                    "password": HASHED_PASSWORDS["parent"],
                },
            )

            Parent.objects.update_or_create(
                user=user,
                defaults={
                    "student": student,
                    "relation_ship": "Guardian",
                },
            )

            self.credentials.append(
                (
                    school.name,
                    "Parent",
                    username,
                    DEFAULT_PASSWORDS["parent"],
                )
            )

    # =========================================================
    # SESSION
    # =========================================================

    def create_session(self, school):

        session, _ = Session.objects.update_or_create(
            school=school,
            session="2026",
            defaults={
                "is_current": True,
            },
        )

        return session

    # =========================================================
    # TERM
    # =========================================================

    def create_term(self, school, session):

        term, _ = Term.objects.update_or_create(
            school=school,
            session=session,
            name="T1",
            defaults={
                "is_current": True,
            },
        )

        return term

    # =========================================================
    # FEES
    # =========================================================

    def create_fees(
        self,
        school,
        students,
        session,
        term,
    ):

        fees = []

        for student in students:

            fees.append(
                SchoolFee(
                    school=school,
                    student=student,
                    session=session,
                    term=term,
                    description="Term 1 Fees",
                    amount_due=Decimal("1500.00"),
                    discount=Decimal("0.00"),
                    due_date=timezone.localdate() + timedelta(days=14),
                    status=FEE_STATUS_PARTIAL,
                )
            )

        fee_objs = SchoolFee.objects.bulk_create(
            fees,
            batch_size=500,
        )

        payments = []

        for fee in fee_objs:

            payments.append(
                FeePayment(
                    fee=fee,
                    reference=f"{fee.school.subdomain}-{fee.id}",
                    amount=Decimal("500.00"),
                    paid_on=timezone.localdate(),
                    method="cash",
                )
            )

        FeePayment.objects.bulk_create(
            payments,
            batch_size=500,
        )

    # =========================================================
    # PRINT CREDENTIALS
    # =========================================================

    def print_credentials(self):

        self.stdout.write("")
        self.stdout.write("=" * 120)

        self.stdout.write(
            self.style.SUCCESS(
                "📋 GENERATED LOGIN CREDENTIALS"
            )
        )

        self.stdout.write("=" * 120)

        for school, role, username, password in self.credentials:

            self.stdout.write(
                f"{school:<30} | "
                f"{role:<15} | "
                f"{username:<40} | "
                f"{password}"
            )

        self.stdout.write("=" * 120)

    # =========================================================
    # EXPORT CREDENTIALS
    # =========================================================

    def save_credentials_to_file(self):

        output_dir = os.path.join(
            "media",
            "seed_credentials",
        )

        os.makedirs(output_dir, exist_ok=True)

        txt_file = os.path.join(
            output_dir,
            "credentials.txt",
        )

        csv_file = os.path.join(
            output_dir,
            "credentials.csv",
        )

        with open(txt_file, "w", encoding="utf-8") as f:

            f.write("LEARNSPHERE GENERATED CREDENTIALS\n")
            f.write("=" * 120)
            f.write("\n\n")

            for school, role, username, password in self.credentials:

                f.write(
                    f"{school:<30} | "
                    f"{role:<15} | "
                    f"{username:<40} | "
                    f"{password}\n"
                )

        with open(csv_file, "w", newline="", encoding="utf-8") as f:

            writer = csv.writer(f)

            writer.writerow([
                "School",
                "Role",
                "Username",
                "Password",
            ])

            for row in self.credentials:
                writer.writerow(row)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"📁 Credentials exported:\n"
                f"   - {txt_file}\n"
                f"   - {csv_file}"
            )
        )