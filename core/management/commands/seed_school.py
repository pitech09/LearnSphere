from datetime import timedelta
from decimal import Decimal
import csv
import os
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password

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

STUDENTS_PER_SCHOOL = 10
TEACHERS_PER_SCHOOL = 5

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
    {"name": "Green Valley High School", "subdomain": "green-valley"},
    {"name": "Blue Mountain Academy", "subdomain": "blue-mountain"},
]


# =========================================================
# COMMAND
# =========================================================

class Command(BaseCommand):

    help = "LearnSphere LMS Full Seeder"

    def handle(self, *args, **options):

        self.credentials = []

        self.stdout.write("\n🚀 STARTING LEARNSPHERE SEED...\n")

        self.create_platform_owner()

        for school_data in SCHOOLS:
            self.seed_school(school_data)

        self.export_credentials()

        self.stdout.write("\n✅ SEED COMPLETE\n")

    # =====================================================
    # MAIN PIPELINE
    # =====================================================

    def seed_school(self, data):

        school = self.create_school(data)

        self.stdout.write(
            self.style.WARNING(f"\n🏫 Seeding {school.name}...")
        )

        # 👇 Admin + Principal
        self.create_school_admin_and_principal(school)

        teachers = self.create_teachers(school)

        classes = self.create_classes(school, teachers)

        students = self.create_students(school, classes)

        subjects = self.create_subjects(school, teachers)

        session = self.create_session(school)

        term = self.create_term(school, session)

        self.assign_student_subjects(
            school,
            students,
            subjects,
        )

        self.create_parents(school, students)

    # =====================================================
    # SCHOOL
    # =====================================================

    def create_school(self, data):

        school, _ = School.objects.update_or_create(
            subdomain=data["subdomain"],
            defaults={
                "name": data["name"],
                "email": f"admin@{data['subdomain']}.test",
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

    # =====================================================
    # PLATFORM OWNER
    # =====================================================

    def create_platform_owner(self):

        username, password, first, last = PLATFORM_OWNER

        User.objects.update_or_create(
            username=username,
            defaults={
                "first_name": first,
                "last_name": last,
                "email": "owner@learnsphere.test",
                "is_staff": True,
                "is_superuser": True,
                "password": make_password(password),
            },
        )

        self.credentials.append(("Platform", "Owner", username, password))

    # =====================================================
    # ADMIN + PRINCIPAL
    # =====================================================

    def create_school_admin_and_principal(self, school):

        admin_username = f"{school.subdomain}_admin"
        admin_password = "Admin123!"

        User.objects.update_or_create(
            username=admin_username,
            defaults={
                "school": school,
                "first_name": "School",
                "last_name": "Admin",
                "email": f"{admin_username}@test.com",
                "is_staff": True,
                "is_active": True,
                "password": make_password(admin_password),
            },
        )

        self.credentials.append(
            (school.name, "Admin", admin_username, admin_password)
        )

        principal_username = f"{school.subdomain}_principal"
        principal_password = "Principal123!"

        User.objects.update_or_create(
            username=principal_username,
            defaults={
                "school": school,
                "first_name": "School",
                "last_name": "Principal",
                "email": f"{principal_username}@test.com",
                "is_staff": True,
                "is_active": True,
                "password": make_password(principal_password),
            },
        )

        self.credentials.append(
            (school.name, "Principal", principal_username, principal_password)
        )

    # =====================================================
    # TEACHERS
    # =====================================================

    def create_teachers(self, school):

        teachers = []

        for i in range(TEACHERS_PER_SCHOOL):

            username = f"{school.subdomain}_teacher_{i}"
            password = "Teacher123!"

            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "school": school,
                    "first_name": f"T{i}",
                    "last_name": "Teacher",
                    "is_staff": True,
                    "is_lecturer": True,
                    "password": make_password(password),
                },
            )

            teachers.append(user)
            self.credentials.append((school.name, "Teacher", username, password))

        return teachers

    # =====================================================
    # CLASSES
    # =====================================================

    def create_classes(self, school, teachers):

        classes = []
        levels = ["F1", "F2", "F3", "F4", "F5"]

        for i, level in enumerate(levels):

            teacher = teachers[i % len(teachers)]

            school_class, _ = SchoolClass.objects.update_or_create(
                school=school,
                level=level,
                name=f"{level}A",
                defaults={
                    "class_teacher": teacher,
                    "is_active": True,
                },
            )

            classes.append(school_class)

        return classes

    # =====================================================
    # STUDENTS
    # =====================================================

    def create_students(self, school, classes):

        students = []

        for i in range(STUDENTS_PER_SCHOOL):

            assigned_class = classes[i % len(classes)]

            username = f"{school.subdomain}_student_{i}"
            password = "Student123!"

            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "school": school,
                    "first_name": f"S{i}",
                    "last_name": "Student",
                    "is_student": True,
                    "is_active": True,
                    "password": make_password(password),
                },
            )

            student, _ = Student.objects.update_or_create(
                student=user,
                defaults={
                    "level": assigned_class.level,
                    "student_class": assigned_class,
                },
            )

            students.append(student)

            self.credentials.append((school.name, "Student", username, password))

        return students

    # =====================================================
    # SUBJECTS
    # =====================================================

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

    # =====================================================
    # STUDENT ↔ SUBJECT LINK
    # =====================================================

    def assign_student_subjects(self, school, students, subjects):

        bulk = []

        existing = set(
            TakenCourse.objects.filter(school=school)
            .values_list("student_id", "course_id")
        )

        for student in students:
            for subject in subjects:

                if (student.id, subject.id) in existing:
                    continue

                bulk.append(
                    TakenCourse(
                        school=school,
                        student=student,
                        course=subject,
                        quarter="Q1",
                        assignment=random.randint(40, 95),
                        mid_exam=random.randint(40, 95),
                        quiz=random.randint(40, 95),
                        attendance=random.randint(50, 100),
                        final_exam=random.randint(40, 95),
                    )
                )

        TakenCourse.objects.bulk_create(bulk, batch_size=500)

    # =====================================================
    # PARENTS
    # =====================================================

    def create_parents(self, school, students):

        for i, student in enumerate(students):

            username = f"{school.subdomain}_parent_{i}"
            password = "Parent123!"

            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "school": school,
                    "first_name": f"P{i}",
                    "last_name": "Parent",
                    "is_parent": True,
                    "password": make_password(password),
                },
            )

            Parent.objects.update_or_create(
                user=user,
                defaults={
                    "student": student,
                    "relation_ship": "Guardian",
                },
            )

            self.credentials.append((school.name, "Parent", username, password))

    # =====================================================
    # SESSION
    # =====================================================

    def create_session(self, school):

        return Session.objects.update_or_create(
            school=school,
            session="2026",
            defaults={"is_current": True},
        )[0]

    # =====================================================
    # TERM
    # =====================================================

    def create_term(self, school, session):

        return Term.objects.update_or_create(
            school=school,
            session=session,
            name="T1",
            defaults={"is_current": True},
        )[0]

    # =====================================================
    # EXPORT CREDENTIALS
    # =====================================================

    def export_credentials(self):

        os.makedirs("media/seed", exist_ok=True)

        with open("media/seed/credentials.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["School", "Role", "Username", "Password"])
            writer.writerows(self.credentials)

        self.stdout.write("📁 credentials exported")