from datetime import timedelta
from decimal import Decimal
import csv
import os
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

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


# =========================================================
# CONFIG
# =========================================================

STUDENTS_PER_SCHOOL = 30
TEACHERS_PER_SCHOOL = 8

SUBJECT_POOL = [
    ("Mathematics", "MATH"),
    ("English", "ENG"),
    ("Science", "SCI"),
    ("History", "HIS"),
    ("Geography", "GEO"),
    ("Computer Studies", "CS"),
    ("Life Skills", "LS"),
]

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

    help = "LearnSphere LMS Stress Seeder"

    @transaction.atomic
    def handle(self, *args, **options):

        self.credentials = []

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("🚀 STARTING LEARNSPHERE STRESS SEED...")
        )
        self.stdout.write("")

        self.create_platform_owner()

        for school_data in SCHOOLS:
            self.seed_school(school_data)

        self.print_credentials()
        self.save_credentials_to_file()

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("✅ SEEDING COMPLETE")
        )
        self.stdout.write("")

    # =========================================================
    # SCHOOL SEEDER
    # =========================================================

    def seed_school(self, data):

        school = self.create_school(data)

        self.stdout.write(
            self.style.WARNING(f"\n🏫 Seeding {school.name}...")
        )

        teachers = self.create_teachers(school)

        classes = self.create_classes(
            school=school,
            teachers=teachers,
        )

        students = self.create_students(
            school=school,
            classes=classes,
        )

        self.create_parents(
            school=school,
            students=students,
        )

        subjects = self.create_subjects(
            school=school,
            teachers=teachers,
        )

        session = self.create_session(school)

        term = self.create_term(
            school=school,
            session=session,
        )

        self.create_results(
            school=school,
            students=students,
            subjects=subjects,
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
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        user.set_password(password)
        user.save()

        self.credentials.append(
            ("Platform", "Owner", username, password)
        )

    # =========================================================
    # TEACHERS
    # =========================================================

    def create_teachers(self, school):

        teachers = []

        for i in range(TEACHERS_PER_SCHOOL):

            username = f"{school.subdomain}_teacher_{i}"
            password = "Teacher123!"

            self.stdout.write(
                f"👨‍🏫 Creating teacher {i + 1}/{TEACHERS_PER_SCHOOL}"
            )

            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "school": school,
                    "first_name": f"Teacher{i}",
                    "last_name": "Staff",
                    "email": f"{username}@test.com",
                    "phone": "+26650000000",
                    "is_staff": True,
                    "is_lecturer": True,
                    "is_active": True,
                },
            )

            user.set_password(password)
            user.save()

            teachers.append(user)

            self.credentials.append(
                (school.name, "Teacher", username, password)
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
    # STUDENTS
    # =========================================================

    def create_students(self, school, classes):

        students = []

        for i in range(STUDENTS_PER_SCHOOL):

            username = f"{school.subdomain}_student_{i}"
            password = "Student123!"

            self.stdout.write(
                f"🎓 Creating student {i + 1}/{STUDENTS_PER_SCHOOL}"
            )

            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "school": school,
                    "first_name": f"Student{i}",
                    "last_name": "Learner",
                    "email": f"{username}@test.com",
                    "phone": "+26650000000",
                    "is_student": True,
                    "is_active": True,
                },
            )

            user.set_password(password)
            user.save()

            assigned_class = random.choice(classes)

            student, _ = Student.objects.update_or_create(
                student=user,
                defaults={
                    "level": assigned_class.level,
                    "student_class": assigned_class,
                },
            )

            students.append(student)

            self.credentials.append(
                (school.name, "Student", username, password)
            )

        return students

    # =========================================================
    # PARENTS
    # =========================================================

    def create_parents(self, school, students):

        for i, student in enumerate(students):

            username = f"{school.subdomain}_parent_{i}"
            password = "Parent123!"

            self.stdout.write(
                f"👨‍👩‍👧 Creating parent {i + 1}/{len(students)}"
            )

            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "school": school,
                    "first_name": f"Parent{i}",
                    "last_name": "Guardian",
                    "email": f"{username}@test.com",
                    "phone": "+26650000000",
                    "is_parent": True,
                    "is_active": True,
                },
            )

            user.set_password(password)
            user.save()

            Parent.objects.update_or_create(
                user=user,
                defaults={
                    "student": student,
                    "relation_ship": "Guardian",
                },
            )

            self.credentials.append(
                (school.name, "Parent", username, password)
            )

    # =========================================================
    # SUBJECTS
    # =========================================================

    def create_subjects(self, school, teachers):

        subjects = []

        for title, code in SUBJECT_POOL:

            teacher = random.choice(teachers)

            subject, _ = Subject.objects.update_or_create(
                school=school,
                code=f"{school.subdomain}-{code}",
                defaults={
                    "title": title,
                    "teacher": teacher,
                },
            )

            subjects.append(subject)

        return subjects

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
    # RESULTS
    # =========================================================

    def create_results(self, school, students, subjects):

        bulk = []

        for student in students:
            for subject in subjects:

                bulk.append(
                    TakenCourse(
                        school=school,
                        student=student,
                        course=subject,
                        quarter="Q1",
                        assignment=Decimal(random.randint(40, 95)),
                        mid_exam=Decimal(random.randint(40, 95)),
                        quiz=Decimal(random.randint(40, 95)),
                        attendance=Decimal(random.randint(50, 100)),
                        final_exam=Decimal(random.randint(40, 95)),
                    )
                )

        TakenCourse.objects.bulk_create(
            bulk,
            batch_size=100,
        )

    # =========================================================
    # FEES
    # =========================================================

    def create_fees(self, school, students, session, term):

        fees = []

        for student in students:

            fees.append(
                SchoolFee(
                    school=school,
                    student=student,
                    session=session,
                    term=term,
                    description="Term 1 fees",
                    amount_due=Decimal("1500.00"),
                    discount=Decimal("0.00"),
                    due_date=timezone.localdate() + timedelta(days=14),
                    status=FEE_STATUS_PARTIAL,
                )
            )

        fee_objs = SchoolFee.objects.bulk_create(
            fees,
            batch_size=100,
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
            batch_size=100,
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
                f"{role:<10} | "
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

        # TXT
        with open(txt_file, "w", encoding="utf-8") as f:

            f.write("LEARNSPHERE GENERATED CREDENTIALS\n")
            f.write("=" * 120)
            f.write("\n\n")

            for school, role, username, password in self.credentials:

                f.write(
                    f"{school:<30} | "
                    f"{role:<10} | "
                    f"{username:<40} | "
                    f"{password}\n"
                )

        # CSV
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