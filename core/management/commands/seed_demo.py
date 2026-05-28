import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Student
from core.models import School, SchoolClass
from course.models import Subject

User = get_user_model()

SUBJECTS = [
    ("Mathematics", "MATH101"),
    ("English Language", "ENG101"),
    ("Science", "SCI101"),
    ("History", "HIST101"),
    ("Geography", "GEO101"),
    ("Art", "ART101"),
    ("Physical Education", "PE101"),
]

# (class name, level)
CLASS_NAMES = [
    ("Form 1A", "F1"),
    ("Form 1B", "F1"),
    ("Form 2A", "F2"),
    ("Form 2B", "F2"),
    ("Form 3A", "F3"),
]

SCHOOLS = [
    "Greenwood High School",
    "Sunrise Academy",
    "Riverside College",
]

DEFAULT_PASSWORD = "password123"

class Command(BaseCommand):
    help = "Seed 3 schools with 15 students, 8 teachers, 1 principal, 5 classes, 7 subjects per class"

    def handle(self, *args, **options):
        for school_name in SCHOOLS:
            self.stdout.write(f"\nSeeding school: {school_name}")

            # Create school
            school, created = School.objects.get_or_create(
                name=school_name,
                defaults={
                    'email': f"info@{school_name.lower().replace(' ', '')}.com",
                    'phone': '+1234567890',
                    'address': f'123 Main St, {school_name}',
                    'status': 'active',
                    'plan': 'starter',
                    'is_active': True,
                }
            )
            if not created:
                self.stdout.write(f"  School '{school_name}' already exists, skipping creation.")
                continue

            # Create principal (admin)
            principal_username = f"principal_{school.id}"
            principal, _ = User.objects.get_or_create(
                username=principal_username,
                defaults={
                    'first_name': 'Principal',
                    'last_name': school_name.split()[0],
                    'email': f"{principal_username}@{school_name.lower().replace(' ', '')}.com",
                    'is_superuser': True,
                    'is_staff': True,
                    'is_lecturer': False,
                    'is_student': False,
                    'school': school,
                }
            )
            if principal.school != school:
                principal.school = school
            principal.set_password(DEFAULT_PASSWORD)
            principal.save()
            self.stdout.write(self.style.SUCCESS(f"  Principal: {principal_username} / password: {DEFAULT_PASSWORD}"))

            # Create 8 teachers
            teachers = []
            for i in range(1, 9):
                username = f"teacher_{school.id}_{i}"
                user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': f"Teacher{i}",
                        'last_name': school_name.split()[0],
                        'email': f"{username}@{school_name.lower().replace(' ', '')}.com",
                        'is_lecturer': True,
                        'school': school,
                    }
                )
                if user.school != school:
                    user.school = school
                user.set_password(DEFAULT_PASSWORD)
                user.save()
                teachers.append(user)
                self.stdout.write(f"  Teacher: {username} / password: {DEFAULT_PASSWORD}")

            # Create 15 students
            students = []
            for i in range(1, 16):
                username = f"student_{school.id}_{i}"
                user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': f"Student{i}",
                        'last_name': school_name.split()[0],
                        'email': f"{username}@{school_name.lower().replace(' ', '')}.com",
                        'is_student': True,
                        'school': school,
                    }
                )
                if user.school != school:
                    user.school = school
                user.set_password(DEFAULT_PASSWORD)
                user.save()
                student, _ = Student.objects.get_or_create(
                    student=user,
                    defaults={}
                )
                students.append(student)
            self.stdout.write(f"  Created {len(students)} students (all password: {DEFAULT_PASSWORD})")

            # Create classes (no stream field anymore)
            classes = []
            for class_name, level in CLASS_NAMES:
                class_obj, _ = SchoolClass.objects.get_or_create(
                    school=school,
                    name=class_name,
                    defaults={
                        'level': level,
                        'is_active': True,
                        'class_teacher': random.choice(teachers) if teachers else None,
                    }
                )
                classes.append(class_obj)
            self.stdout.write(f"  Created {len(classes)} classes")

            # Assign students to classes (distribute evenly)
            for idx, student in enumerate(students):
                class_obj = classes[idx % len(classes)]
                student.student_class = class_obj
                student.save()
            self.stdout.write(f"  Assigned students to classes")

            # Create subjects for each class
            total_subjects = 0
            for class_obj in classes:
                for title, code in SUBJECTS:
                    teacher = random.choice(teachers) if teachers else None
                    subject, _ = Subject.objects.get_or_create(
                        school=school,
                        class_assigned=class_obj,
                        code=code,
                        defaults={
                            'title': title,
                            'slug': f"{code.lower()}_{class_obj.name.lower().replace(' ', '')}",
                            'summary': f"{title} for {class_obj.name}",
                            'teacher': teacher,
                        }
                    )
                    total_subjects += 1
            self.stdout.write(f"  Created {total_subjects} subjects (7 per class)")

            self.stdout.write(self.style.SUCCESS(f"  Successfully seeded school: {school_name}\n"))

        self.stdout.write(self.style.SUCCESS("Seeding completed for all schools."))