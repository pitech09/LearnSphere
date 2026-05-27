import csv
import random

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Parent, Student, User
from core.models import School, SchoolClass
from course.models import Subject
from result.models import TakenCourse


DEFAULT_PASSWORD = "Student123!"
HASHED_PASSWORD = make_password(DEFAULT_PASSWORD)


class Command(BaseCommand):

    help = "Import students from CSV"

    def add_arguments(self, parser):

        parser.add_argument(
            "school_subdomain",
            type=str,
        )

        parser.add_argument(
            "csv_file",
            type=str,
        )

    @transaction.atomic
    def handle(self, *args, **options):

        school_subdomain = options["school_subdomain"]
        csv_file = options["csv_file"]

        school = School.objects.get(
            subdomain=school_subdomain
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"📥 Importing students into {school.name}"
            )
        )

        created_students = 0

        with open(csv_file, newline="", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:

                try:

                    class_name = row["class_name"]

                    school_class = SchoolClass.objects.get(
                        school=school,
                        name=class_name,
                    )

                    username = (
                        row["admission_number"]
                        .lower()
                        .replace(" ", "")
                    )

                    # =========================================
                    # CREATE USER
                    # =========================================

                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            "school": school,
                            "first_name": row["first_name"],
                            "last_name": row["last_name"],
                            "email": row["email"],
                            "phone": row["phone"],
                            "is_student": True,
                            "is_active": True,
                            "password": HASHED_PASSWORD,
                        },
                    )

                    # =========================================
                    # CREATE STUDENT
                    # =========================================

                    student, _ = Student.objects.get_or_create(
                        student=user,
                        defaults={
                            "level": row["class_level"],
                            "student_class": school_class,
                            "gender": row["gender"],
                            "address": row["address"],
                            "admission_number": row[
                                "admission_number"
                            ],
                        },
                    )

                    # =========================================
                    # CREATE PARENT
                    # =========================================

                    parent_username = (
                        f"parent_{username}"
                    )

                    parent_user, _ = User.objects.get_or_create(
                        username=parent_username,
                        defaults={
                            "school": school,
                            "first_name": row[
                                "parent_first_name"
                            ],
                            "last_name": row[
                                "parent_last_name"
                            ],
                            "email": row[
                                "parent_email"
                            ],
                            "phone": row[
                                "parent_phone"
                            ],
                            "is_parent": True,
                            "is_active": True,
                            "password": HASHED_PASSWORD,
                        },
                    )

                    Parent.objects.get_or_create(
                        user=parent_user,
                        defaults={
                            "student": student,
                            "relation_ship": "Guardian",
                        },
                    )

                    # =========================================
                    # ASSIGN SUBJECTS
                    # =========================================

                    subjects = Subject.objects.filter(
                        school=school,
                        school_class=school_class,
                    )

                    taken_courses = []

                    for subject in subjects:

                        taken_courses.append(
                            TakenCourse(
                                school=school,
                                student=student,
                                course=subject,
                                quarter="Q1",
                            )
                        )

                    TakenCourse.objects.bulk_create(
                        taken_courses,
                        ignore_conflicts=True,
                    )

                    created_students += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Imported "
                            f"{row['first_name']} "
                            f"{row['last_name']}"
                        )
                    )

                except Exception as e:

                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Error importing "
                            f"{row.get('first_name')} "
                            f"{row.get('last_name')} "
                            f"-> {str(e)}"
                        )
                    )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"🎉 Successfully imported "
                f"{created_students} students"
            )
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                f"🔑 Default Password: "
                f"{DEFAULT_PASSWORD}"
            )
        )


        ''' USAGE
        python manage.py import_students \
    green-valley \
    students_import.csv
        '''