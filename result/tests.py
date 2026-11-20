from decimal import Decimal

from django.test import TestCase

from accounts.models import Student, User
from core.models import School
from course.models import Subject
from .models import TakenCourse


class TakenCourseGradingTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Grade Test School",
            assignment_weight=20,
            mid_exam_weight=20,
            quiz_weight=0,
            attendance_weight=0,
            final_exam_weight=60,
        )
        user = User.objects.create_user(
            username="student1",
            school=self.school,
            is_student=True,
        )
        self.student = Student.objects.create(student=user, level="F1")
        self.subject = Subject.objects.create(
            school=self.school,
            title="Mathematics",
            code="MATH1",
        )

    def test_default_high_school_weights(self):
        course = TakenCourse.objects.create(
            student=self.student,
            course=self.subject,
            assignment=80,
            mid_exam=70,
            quiz=0,
            attendance=0,
            final_exam=60,
        )
        self.assertEqual(course.total, Decimal("66.00"))

    def test_quiz_can_be_enabled_as_a_component(self):
        self.school.quiz_weight = 20
        self.school.final_exam_weight = 40
        self.school.save()
        course = TakenCourse.objects.create(
            student=self.student,
            course=self.subject,
            assignment=80,
            mid_exam=70,
            quiz=100,
            final_exam=60,
        )
        self.assertEqual(course.total, Decimal("74.00"))
