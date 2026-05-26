from datetime import timedelta
from decimal import Decimal
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


PLATFORM_OWNER = ("platform_owner", "PlatformOwner123!", "Platform", "Owner")

SCHOOLS = [
    {
        "name": "Green Valley High School",
        "subdomain": "green-valley",
        "admin": ("green_admin", "GreenAdmin123!", "Grace", "Mokoena"),
        "teacher": ("green_teacher", "GreenTeacher123!", "Thabo", "Ndlovu"),
        "student": ("green_student", "GreenStudent123!", "Lerato", "Molefe"),
        "parent": ("green_parent", "GreenParent123!", "Mpho", "Molefe"),
    },
    {
        "name": "Blue Mountain Academy",
        "subdomain": "blue-mountain",
        "admin": ("blue_admin", "BlueAdmin123!", "Naledi", "Dlamini"),
        "teacher": ("blue_teacher", "BlueTeacher123!", "Kabelo", "Maseko"),
        "student": ("blue_student", "BlueStudent123!", "Neo", "Khama"),
        "parent": ("blue_parent", "BlueParent123!", "Palesa", "Khama"),
    },
]


class Command(BaseCommand):
    help = "Seeder Engine (single-file architecture)"

    # ================= ENTRY =================
    @transaction.atomic
    def handle(self, *args, **options):
        self.credentials = []

        self.create_platform_owner()

        for school_data in SCHOOLS:
            self.seed_school(school_data)

        self.print_credentials()

    # ================= ENGINE =================
    def seed_school(self, school_data):
        school = self.create_school(school_data)

        users = self.create_users(school, school_data)

        school_class = self.create_classes(school, users["teacher"])
        session = self.create_session(school)
        term = self.create_term(school, session)

        student = self.create_student(school, users["student"], school_class)
        self.create_parent(users["parent"], student)

        subjects = self.create_subjects(school, school_class, users["teacher"])
        self.create_results(school, student, subjects)

        fee = self.create_fee(school, student, session, term)
        self.create_payment(fee, users["admin"])

        self.store_credentials(school, school_data, users)

    # ================= SCHOOL =================
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

    # ================= USERS =================
    def create_users(self, school, data):
        return {
            "admin": self.upsert_user(school, data["admin"], is_staff=True, is_superuser=True),
            "teacher": self.upsert_user(school, data["teacher"], is_staff=True, is_lecturer=True),
            "student": self.upsert_user(school, data["student"], is_student=True),
            "parent": self.upsert_user(school, data["parent"], is_parent=True),
        }

    def upsert_user(self, school, data, **flags):
        username, password, first, last = data

        user, created = User.objects.update_or_create(
            username=username,
            defaults={
                "school": school,
                "first_name": first,
                "last_name": last,
                "email": f"{username}@{school.subdomain}.learnsphere.test",
                "phone": "+26650000000",
                "is_staff": flags.get("is_staff", False),
                "is_superuser": flags.get("is_superuser", False),
                "is_lecturer": flags.get("is_lecturer", False),
                "is_student": flags.get("is_student", False),
                "is_parent": flags.get("is_parent", False),
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()

        return user

    # ================= PLATFORM OWNER =================
    def create_platform_owner(self):
        username, password, first, last = PLATFORM_OWNER

        user, created = User.objects.update_or_create(
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

        if created:
            user.set_password(password)
            user.save()

        self.credentials.append(("Platform", "Owner", username, password))

    # ================= ACADEMICS =================
    def create_classes(self, school, teacher):
        class_name, level = "F1A", "F1"

        school_class, _ = SchoolClass.objects.update_or_create(
            school=school,
            level=level,
            name=class_name,
            defaults={"class_teacher": teacher, "is_active": True},
        )
        return school_class

    def create_session(self, school):
        session, _ = Session.objects.update_or_create(
            school=school,
            session="2026",
            defaults={"is_current": True},
        )
        return session

    def create_term(self, school, session):
        term, _ = Term.objects.update_or_create(
            school=school,
            session=session,
            name="T1",
            defaults={"is_current": True},
        )
        return term

    # ================= STUDENTS =================
    def create_student(self, school, user, school_class):
        student, _ = Student.objects.update_or_create(
            student=user,
            defaults={
                "level": school_class.level,
                "student_class": school_class,
            },
        )
        return student

    def create_parent(self, parent_user, student):
        Parent.objects.update_or_create(
            user=parent_user,
            defaults={
                "student": student,
                "first_name": parent_user.first_name,
                "last_name": parent_user.last_name,
                "phone": parent_user.phone,
                "email": parent_user.email,
                "relation_ship": "Father",
            },
        )

    # ================= SUBJECTS + RESULTS =================
    def create_subjects(self, school, school_class, teacher):
        subject_pool = [
            ("Mathematics", "MATH"),
            ("English", "ENG"),
            ("Science", "SCI"),
            ("History", "HIS"),
            ("Geography", "GEO"),
            ("Computer Studies", "CS"),
            ("Life Skills", "LS"),
        ]

        subjects = []

        for title, code in subject_pool:
            subject, _ = Subject.objects.update_or_create(
                school=school,
                class_assigned=school_class,
                code=f"{school.subdomain}-{code}",
                defaults={
                    "title": title,
                    "teacher": teacher,
                },
            )
            subjects.append(subject)

        return subjects

    def create_results(self, school, student, subjects):
        for subject in subjects:
            TakenCourse.objects.update_or_create(
                school=school,
                student=student,
                course=subject,
                quarter="Q1",
                defaults={
                    "assignment": Decimal(random.randint(50, 95)),
                    "mid_exam": Decimal(random.randint(50, 95)),
                    "quiz": Decimal(random.randint(50, 95)),
                    "attendance": Decimal(random.randint(60, 100)),
                    "final_exam": Decimal(random.randint(50, 95)),
                },
            )

    # ================= FINANCE =================
    def create_fee(self, school, student, session, term):
        fee, _ = SchoolFee.objects.update_or_create(
            school=school,
            student=student,
            session=session,
            term=term,
            description="Term 1 tuition fees",
            defaults={
                "amount_due": Decimal("1500.00"),
                "discount": Decimal("0.00"),
                "due_date": timezone.localdate() + timedelta(days=14),
                "status": FEE_STATUS_PARTIAL,
            },
        )
        return fee

    def create_payment(self, fee, admin):
        FeePayment.objects.update_or_create(
            fee=fee,
            reference=f"{fee.school.subdomain.upper()}-T1-DEPOSIT",
            defaults={
                "amount": Decimal("500.00"),
                "paid_on": timezone.localdate(),
                "method": "cash",
                "received_by": admin,
                "notes": "Seed payment",
            },
        )

    # ================= CREDENTIALS =================
    def store_credentials(self, school, data, users):
        for role, user in users.items():
            self.credentials.append(
                (school.name, role, user.username, "HIDDEN_IF_EXISTING")
            )

    def print_credentials(self):
        self.stdout.write(self.style.SUCCESS("Seeder Engine executed 🚀"))
        for school, role, username, password in self.credentials:
            self.stdout.write(f"- {school} | {role}: {username} / {password}")