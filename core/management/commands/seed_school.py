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


# ================= CONFIG =================
STRESS_MODE = True

STUDENTS_PER_SCHOOL = 200
TEACHERS_PER_SCHOOL = 12
SUBJECT_POOL = [
    ("Mathematics", "MATH"),
    ("English", "ENG"),
    ("Science", "SCI"),
    ("History", "HIS"),
    ("Geography", "GEO"),
    ("Computer Studies", "CS"),
    ("Life Skills", "LS"),
]

PLATFORM_OWNER = ("platform_owner", "PlatformOwner123!", "Platform", "Owner")

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


# ================= COMMAND =================
class Command(BaseCommand):
    help = "FULL LMS Stress Seeder (single script)"

    @transaction.atomic
    def handle(self, *args, **options):

        self.credentials = []

        self.create_platform_owner()

        for school_data in SCHOOLS:
            self.seed_school(school_data)

        self.print_credentials()

    # ================= SCHOOL =================
    def seed_school(self, data):

        school = self.create_school(data)

        teachers = self.create_teachers(school)
        classes = self.create_classes(school, teachers)

        students = self.create_students(school, classes)
        parents = self.create_parents(school, students)

        subjects = self.create_subjects(school, teachers)

        session = self.create_session(school)
        term = self.create_term(school, session)

        self.create_results(school, students, subjects)
        self.create_fees(school, students, session, term)

        self.credentials.append((school.name, "SYSTEM", "STRESS MODE", "ACTIVE"))

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

    # ================= TEACHERS =================
    def create_teachers(self, school):
        teachers = []

        for i in range(TEACHERS_PER_SCHOOL):

            user, created = User.objects.update_or_create(
                username=f"{school.subdomain}_teacher_{i}",
                defaults={
                    "school": school,
                    "first_name": f"Teacher{i}",
                    "last_name": "Staff",
                    "email": f"t{i}@{school.subdomain}.test",
                    "phone": "+26650000000",
                    "is_staff": True,
                    "is_lecturer": True,
                    "is_active": True,
                },
            )

            if created:
                user.set_password("Teacher123!")
                user.save()

            teachers.append(user)

        return teachers

    # ================= CLASSES =================
    def create_classes(self, school, teachers):

        levels = ["F1", "F2", "F3", "F4", "F5"]
        streams = ["A", "B"]

        classes = []
        t = 0

        for level in levels:
            for stream in streams:

                teacher = teachers[t % len(teachers)]
                t += 1

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

    # ================= STUDENTS =================
    def create_students(self, school, classes):

        students = []

        for i in range(STUDENTS_PER_SCHOOL):

            user = User.objects.create(
                username=f"{school.subdomain}_student_{i}",
                first_name=f"Student{i}",
                last_name="Learner",
                school=school,
                is_student=True,
            )
            user.set_password("Student123!")
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

        return students

    # ================= PARENTS =================
    def create_parents(self, school, students):

        parents = []

        for i, student in enumerate(students):

            user = User.objects.create(
                username=f"{school.subdomain}_parent_{i}",
                first_name=f"Parent{i}",
                last_name="Guardian",
                school=school,
                is_parent=True,
            )
            user.set_password("Parent123!")
            user.save()

            Parent.objects.update_or_create(
                user=user,
                defaults={
                    "student": student,
                    "relation_ship": "Guardian",
                },
            )

            parents.append(user)

        return parents

    # ================= SUBJECTS =================
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

    # ================= SESSION / TERM =================
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

    # ================= RESULTS (STRESS BULK) =================
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

        TakenCourse.objects.bulk_create(bulk, batch_size=500)

    # ================= FINANCE =================
    def create_fees(self, school, students, session, term):

        fees = []
        payments = []

        for student in students:

            fee = SchoolFee(
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
            fees.append(fee)

        fee_objs = SchoolFee.objects.bulk_create(fees, batch_size=500)

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

        FeePayment.objects.bulk_create(payments, batch_size=500)

    # ================= OUTPUT =================
    def print_credentials(self):
        self.stdout.write(self.style.SUCCESS(" STRESS SEED COMPLETE"))

        for item in self.credentials:
            self.stdout.write(str(item))