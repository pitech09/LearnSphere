from decimal import Decimal, ROUND_HALF_UP
from django.db import models

from accounts.models import Student
from course.models import Subject as Course


# =========================================================
# GRADING SYSTEM
# =========================================================
A_PLUS = "A+"
A = "A"
A_MINUS = "A-"
B_PLUS = "B+"
B = "B"
B_MINUS = "B-"
C_PLUS = "C+"
C = "C"
C_MINUS = "C-"
D = "D"
F = "F"
NG = "NG"

GRADE_CHOICES = (
    (A_PLUS, "A+"),
    (A, "A"),
    (A_MINUS, "A-"),
    (B_PLUS, "B+"),
    (B, "B"),
    (B_MINUS, "B-"),
    (C_PLUS, "C+"),
    (C, "C"),
    (C_MINUS, "C-"),
    (D, "D"),
    (F, "F"),
    (NG, "NG"),
)

PASS = "PASS"
FAIL = "FAIL"

COMMENT_CHOICES = (
    (PASS, "PASS"),
    (FAIL, "FAIL"),
)

Q1 = "Q1"
Q2 = "Q2"
Q3 = "Q3"
Q4 = "Q4"

QUARTER_CHOICES = (
    (Q1, "Quarter 1"),
    (Q2, "Quarter 2"),
    (Q3, "Quarter 3"),
    (Q4, "Quarter 4"),
)

GRADE_BOUNDARIES = [
    (90, A_PLUS),
    (85, A),
    (80, A_MINUS),
    (75, B_PLUS),
    (70, B),
    (65, B_MINUS),
    (60, C_PLUS),
    (55, C),
    (50, C_MINUS),
    (45, D),
    (0, F),
]

GRADE_POINT_MAPPING = {
    A_PLUS: 4.0,
    A: 4.0,
    A_MINUS: 3.75,
    B_PLUS: 3.5,
    B: 3.0,
    B_MINUS: 2.75,
    C_PLUS: 2.5,
    C: 2.0,
    C_MINUS: 1.75,
    D: 1.0,
    F: 0.0,
    NG: 0.0,
}

TEST_FIELDS = ("assignment", "mid_exam", "quiz")


# =========================================================
# TAKEN COURSE (SUBJECT RESULT)
# =========================================================
class TakenCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="taken_courses"
    )
    quarter = models.CharField(max_length=2, choices=QUARTER_CHOICES, default=Q1)

    assignment = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    mid_exam = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quiz = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    attendance = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_exam = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    total = models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True, editable=False)
    point = models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)
    comment = models.CharField(max_length=10, choices=COMMENT_CHOICES, blank=True, editable=False)

    def __str__(self):
        return f"{self.course.title} - {self.student}"

    # =====================================================
    # TEST AVERAGE
    # =====================================================
    def get_test_average(self):
        test_total = sum(Decimal(getattr(self, field)) for field in TEST_FIELDS)
        return (test_total / Decimal(len(TEST_FIELDS))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # FINAL MARK: 40% TESTS + 60% EXAM
    # =====================================================
    def get_total(self):
        weighted_mark = (
            self.get_test_average() * Decimal("0.40")
            + Decimal(self.final_exam) * Decimal("0.60")
        )
        return weighted_mark.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # =====================================================
    # GRADE CALCULATION
    # =====================================================
    def get_grade(self):
        for boundary, grade in GRADE_BOUNDARIES:
            if self.total >= Decimal(boundary):
                return grade
        return NG

    # =====================================================
    # PASS / FAIL
    # =====================================================
    def get_comment(self):
        return PASS if self.grade not in [F, NG] else FAIL

    # =====================================================
    # POINTS ARE NOT USED FOR HIGH SCHOOL RESULTS
    # =====================================================
    def get_point(self):
        return Decimal("0.00")

    # =====================================================
    # AUTO CALCULATION ON SAVE
    # =====================================================
    def save(self, *args, **kwargs):
        self.total = self.get_total()
        self.grade = self.get_grade()
        self.point = self.get_point()
        self.comment = self.get_comment()
        super().save(*args, **kwargs)


# =========================================================
# RESULT SUMMARY (TERM / YEAR REPORT CARD)
# =========================================================
class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    session = models.CharField(max_length=100, blank=True, null=True)
    quarter = models.CharField(max_length=2, choices=QUARTER_CHOICES, default=Q1)

    total_subjects = models.IntegerField(default=0)
    total_points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    comment = models.CharField(max_length=10, choices=COMMENT_CHOICES, blank=True)

    def __str__(self):
        return f"Result - {self.student} ({self.session}, {self.quarter})"
