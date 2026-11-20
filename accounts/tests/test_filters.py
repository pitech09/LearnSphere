from django.test import TestCase
from accounts.filters import LecturerFilter, StudentFilter
from accounts.models import User, Student
from core.models import School, SchoolClass


class LecturerFilterTestCase(TestCase):
    def setUp(self):
        User.objects.create(
            username="user1",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        User.objects.create(
            username="user2",
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
        )
        User.objects.create(
            username="user3",
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
        )

    def test_username_filter(self):
        filter_set = LecturerFilter(data={"username": "user1"})
        self.assertEqual(len(filter_set.qs), 1)

    def test_name_filter(self):
        filter_set = LecturerFilter(data={"name": "John"})
        self.assertEqual(len(filter_set.qs), 1)

    def test_email_filter(self):
        filter_set = LecturerFilter(data={"email": "example.com"})
        self.assertEqual(
            len(filter_set.qs), 3
        )  # All users should be returned since all have email addresses with "example.com"

    def test_combined_filters(self):
        filter_set = LecturerFilter(data={"name": "Doe", "email": "example.com"})
        self.assertEqual(
            len(filter_set.qs), 2
        )  # Both John Doe and Jane Doe should be returned

        filter_set = LecturerFilter(data={"name": "Alice", "email": "example.com"})
        self.assertEqual(
            len(filter_set.qs), 1
        )  # 1 user matches Alice with "example.com" in the email

    def test_no_filters(self):
        filter_set = LecturerFilter(data={})
        self.assertEqual(
            len(filter_set.qs), 3
        )  # All users should be returned since no filters are applied


class StudentFilterTestCase(TestCase):
    def setUp(self):
        school = School.objects.create(name="Test High School")
        school_class = SchoolClass.objects.create(
            school=school,
            name="Form 1A",
            level="F1",
        )

        Student.objects.create(
            student=User.objects.create(
                username="student1",
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                school=school,
            ),
            level="F1",
            student_class=school_class,
        )
        Student.objects.create(
            student=User.objects.create(
                username="student2",
                first_name="Jane",
                last_name="Williams",
                email="jane@example.com",
                school=school,
            ),
            level="F1",
            student_class=school_class,
        )
        Student.objects.create(
            student=User.objects.create(
                username="student3",
                first_name="Alice",
                last_name="Smith",
                email="alice@example.com",
                school=school,
            ),
            level="F1",
            student_class=school_class,
        )

    def test_name_filter(self):
        filtered_students = StudentFilter(
            data={"name": "John"}, queryset=Student.objects.all()
        ).qs
        self.assertEqual(filtered_students.count(), 1)

    def test_email_filter(self):
        filter_set = StudentFilter(data={"email": "example.com"})
        self.assertEqual(
            len(filter_set.qs), 3
        )  # All students should be returned since all have email addresses with "example.com"

    def test_class_filter(self):
        filter_set = StudentFilter(data={"student_class": "Form 1A"})
        self.assertEqual(len(filter_set.qs), 3)
