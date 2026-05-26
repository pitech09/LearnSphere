from datetime import timedelta
from decimal import Decimal

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
        "class": ("F1A", "F1"),
        "subjects": [("Mathematics", "GV-MATH-F1"), ("English", "GV-ENG-F1")],
    },
    {
        "name": "Blue Mountain Academy",
        "subdomain": "blue-mountain",
        "admin": ("blue_admin", "BlueAdmin123!", "Naledi", "Dlamini"),
        "teacher": ("blue_teacher", "BlueTeacher123!", "Kabelo", "Maseko"),
        "student": ("blue_student", "BlueStudent123!", "Neo", "Khama"),
        "parent": ("blue_parent", "BlueParent123!", "Palesa", "Khama"),
        "class": ("F1B", "F1"),
        "subjects": [("Science", "BM-SCI-F1"), ("History", "BM-HIS-F1")],
    },
]


class Command(BaseCommand):
    help = "Seed two independent schools with admin, teacher, student, parent, finance, and learning data."

    @transaction.atomic()
    def handle(self, *args, **options):
        credentials = []

        self.upsert_platform_owner(PLATFORM_OWNER)
        credentials.append(("LearnSphere Platform", "Platform Owner", PLATFORM_OWNER[0], PLATFORM_OWNER[1]))

        for school_data in SCHOOLS:
            school, _ = School.objects.update_or_create(
                subdomain=school_data["subdomain"],
                defaults={
                    "name": school_data["name"],
                    "email": f"admin@{school_data['subdomain']}.learnsphere.test",
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

            admin_user = self.upsert_user(school, school_data["admin"], is_staff=True, is_superuser=True)
            teacher = self.upsert_user(school, school_data["teacher"], is_staff=True, is_lecturer=True)
            student_user = self.upsert_user(school, school_data["student"], is_student=True)
            parent_user = self.upsert_user(school, school_data["parent"], is_parent=True)

            class_name, level = school_data["class"]
            school_class, _ = SchoolClass.objects.update_or_create(
                school=school,
                level=level,
                name=class_name,
                defaults={"class_teacher": teacher, "is_active": True},
            )

            session, _ = Session.objects.update_or_create(
                school=school,
                session="2026",
                defaults={"is_current": True, "next_session_begins": timezone.localdate() + timedelta(days=300)},
            )
            Session.objects.filter(school=school, is_current=True).exclude(pk=session.pk).update(is_current=False)

            term, _ = Term.objects.update_or_create(
                school=school,
                session=session,
                name="T1",
                defaults={"is_current": True, "next_begins": timezone.localdate() + timedelta(days=90)},
            )
            Term.objects.filter(school=school, is_current=True).exclude(pk=term.pk).update(is_current=False)

            student, _ = Student.objects.update_or_create(
                student=student_user,
                defaults={"level": level, "student_class": school_class},
            )

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

            subjects = []
            for title, code in school_data["subjects"]:
                subject, _ = Subject.objects.update_or_create(
                    school=school,
                    class_assigned=school_class,
                    code=code,
                    defaults={
                        "title": title,
                        "summary": f"{title} for {school_class.name}",
                        "teacher": teacher,
                    },
                )
                subjects.append(subject)
                TakenCourse.objects.get_or_create(
                    school=school,
                    student=student,
                    course=subject,
                    quarter="Q1",
                    defaults={
                        "assignment": Decimal("70.00"),
                        "mid_exam": Decimal("68.00"),
                        "quiz": Decimal("75.00"),
                        "attendance": Decimal("90.00"),
                        "final_exam": Decimal("72.00"),
                    },
                )

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
            FeePayment.objects.update_or_create(
                fee=fee,
                reference=f"{school.subdomain.upper()}-T1-DEPOSIT",
                defaults={
                    "amount": Decimal("500.00"),
                    "paid_on": timezone.localdate(),
                    "method": "cash",
                    "received_by": admin_user,
                    "notes": "Seed payment",
                },
            )

            for role, data in (
                ("School Admin", school_data["admin"]),
                ("Teacher", school_data["teacher"]),
                ("Student", school_data["student"]),
                ("Parent", school_data["parent"]),
            ):
                credentials.append((school.name, role, data[0], data[1]))

        self.stdout.write(self.style.SUCCESS("Seeded 2 schools with isolated users and operations."))
        self.stdout.write("")
        self.stdout.write("Credentials:")
        for school, role, username, password in credentials:
            self.stdout.write(f"- {school} | {role}: username={username} password={password}")

    def upsert_user(self, school, data, **flags):
        username, password, first_name, last_name = data
        defaults = {
            "school": school,
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{username}@{school.subdomain}.learnsphere.test",
            "phone": "+26650000000",
            "is_staff": flags.get("is_staff", False),
            "is_superuser": flags.get("is_superuser", False),
            "is_lecturer": flags.get("is_lecturer", False),
            "is_student": flags.get("is_student", False),
            "is_parent": flags.get("is_parent", False),
            "is_active": True,
        }
        user, _ = User.objects.update_or_create(username=username, defaults=defaults)
        user.set_password(password)
        user.save()
        return user

    def upsert_platform_owner(self, data):
        username, password, first_name, last_name = data
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "school": None,
                "first_name": first_name,
                "last_name": last_name,
                "email": "owner@learnsphere.test",
                "phone": "+26650000000",
                "is_staff": True,
                "is_superuser": True,
                "is_lecturer": False,
                "is_student": False,
                "is_parent": False,
                "is_active": True,
            },
        )
        user.set_password(password)
        user.save()
        return user
