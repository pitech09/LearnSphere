from decimal import Decimal
from django.db import models
from django.db.models import Q
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, UserManager
from django.urls import reverse
from django.utils.text import slugify

from accounts.models import User


# =========================================================
#  NEWS & EVENTS
# =========================================================

SCHOOL_STATUS_TRIAL = "trial"
SCHOOL_STATUS_ACTIVE = "active"
SCHOOL_STATUS_SUSPENDED = "suspended"

SCHOOL_STATUS_CHOICES = (
    (SCHOOL_STATUS_TRIAL, _("Trial")),
    (SCHOOL_STATUS_ACTIVE, _("Active")),
    (SCHOOL_STATUS_SUSPENDED, _("Suspended")),
)

SCHOOL_PLAN_STARTER = "starter"
SCHOOL_PLAN_GROWTH = "growth"
SCHOOL_PLAN_ENTERPRISE = "enterprise"
SCHOOL_PLAN_UNLIMITED = "unlimited"

SCHOOL_PLAN_CHOICES = (
    (SCHOOL_PLAN_STARTER, _("Starter")),
    (SCHOOL_PLAN_GROWTH, _("Growth")),
    (SCHOOL_PLAN_ENTERPRISE, _("Enterprise")),
    (SCHOOL_PLAN_UNLIMITED, _("Unlimited (One-Time)")),
)

SCHOOL_QUARTER_CHOICES = (
    ("Q1", _("Quarter 1")),
    ("Q2", _("Quarter 2")),
    ("Q3", _("Quarter 3")),
    ("Q4", _("Quarter 4")),
)


class School(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(null=True, blank=True, unique=True)
    subdomain = models.SlugField(null=True, blank=True, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    max_students = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    is_unlimited = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=SCHOOL_STATUS_CHOICES, default=SCHOOL_STATUS_TRIAL)
    plan = models.CharField(max_length=20, choices=SCHOOL_PLAN_CHOICES, default=SCHOOL_PLAN_STARTER)
    subscription_amount = models.DecimalField(max_digits=10, decimal_places=2, default=250)
    last_payment_on = models.DateField(null=True, blank=True)
    next_payment_due_on = models.DateField(null=True, blank=True)
    suspended_reason = models.TextField(blank=True)
    current_quarter = models.CharField(max_length=4, choices=SCHOOL_QUARTER_CHOICES, default="Q1")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            slug = slugify(self.name)
            self.slug = slug
        if not self.subdomain:
            self.subdomain = self.slug
        plan_config = {
            SCHOOL_PLAN_STARTER: {"max_students": 100, "amount": 250, "unlimited": False},
            SCHOOL_PLAN_GROWTH: {"max_students": 300, "amount": 400, "unlimited": False},
            SCHOOL_PLAN_ENTERPRISE: {"max_students": 800, "amount": 750, "unlimited": False},
            SCHOOL_PLAN_UNLIMITED: {"max_students": 0, "amount": 10000, "unlimited": True},
        }
        config = plan_config.get(self.plan, plan_config[SCHOOL_PLAN_STARTER])
        self.max_students = config["max_students"]
        self.subscription_amount = config["amount"]
        self.is_unlimited = config["unlimited"]
        super().save(*args, **kwargs)


POST_NEWS = "news"
POST_EVENT = "event"

POST_CHOICES = (
    (POST_NEWS, _("News")),
    (POST_EVENT, _("Event")),
)

TARGET_ALL = "all"
TARGET_PARENTS = "parents"
TARGET_STUDENTS = "students"
TARGET_TEACHERS = "teachers"

TARGET_CHOICES = (
    (TARGET_ALL, _("Everyone")),
    (TARGET_PARENTS, _("Parents Only")),
    (TARGET_STUDENTS, _("Students Only")),
    (TARGET_TEACHERS, _("Teachers Only")),
)


class NewsAndEventsQuerySet(models.QuerySet):
    def search(self, query=None):
        if not query:
            return self
        return self.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(posted_as__icontains=query)
        ).distinct()


class NewsAndEventsManager(models.Manager):
    def get_queryset(self):
        return NewsAndEventsQuerySet(self.model, using=self._db)

    def search(self, query=None):
        return self.get_queryset().search(query)


class NewsAndEvents(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    posted_as = models.CharField(max_length=10, choices=POST_CHOICES)
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default=TARGET_ALL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NewsAndEventsManager()

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(fields=["school", "-updated_at"], name="news_school_updated_idx"),
            models.Index(fields=["school", "posted_as"], name="news_school_type_idx"),
            models.Index(fields=["school", "target_audience"], name="news_school_target_idx"),
        ]


# =========================================================
# 📅 SESSION (ACADEMIC YEAR)
# =========================================================

class Session(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    session = models.CharField(max_length=200)
    is_current = models.BooleanField(default=False)
    next_session_begins = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.session

    class Meta:
        unique_together = ("school", "session")
        indexes = [
            models.Index(fields=["school", "is_current"], name="session_school_current_idx"),
        ]


# =========================================================
# 📆 TERM (HIGH SCHOOL STRUCTURE)
# =========================================================

TERM_CHOICES = (
    ("T1", _("Term 1")),
    ("T2", _("Term 2")),
    ("T3", _("Term 3")),
    ("T4", _("Term 4")),
)


class Term(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    name = models.CharField(max_length=2, choices=TERM_CHOICES)
    is_current = models.BooleanField(default=False)
    next_begins = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.session.session}"

    class Meta:
        indexes = [
            models.Index(fields=["school", "is_current"], name="term_school_current_idx"),
            models.Index(fields=["school", "session"], name="term_school_session_idx"),
        ]


# =========================================================
# 🧾 ACTIVITY LOG
# =========================================================

class ActivityLog(models.Model):
    school = models.ForeignKey('core.School', on_delete=models.CASCADE, related_name='activity_logs')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['school', '-created_at']),
        ]

    def __str__(self):
        return self.message[:60]


# =========================================================
#  USER SYSTEM
# =========================================================

class CustomUserManager(UserManager):
    def search(self, query=None):
        qs = self.get_queryset()
        if query:
            qs = qs.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
        return qs


# =========================================================
#  SIGNALS
# =========================================================

@receiver(post_save, sender=NewsAndEvents)
def log_news_save(sender, instance, created, **kwargs):
    if instance.school:
        ActivityLog.objects.create(
            school=instance.school,
            message=f"News/Event '{instance.title}' was {'created' if created else 'updated'}."
        )

@receiver(post_delete, sender=NewsAndEvents)
def log_news_delete(sender, instance, **kwargs):
    if instance.school:
        ActivityLog.objects.create(
            school=instance.school,
            message=f"News/Event '{instance.title}' was deleted."
        )

@receiver(post_save, sender=Session)
def log_session_save(sender, instance, created, **kwargs):
    if instance.school:
        ActivityLog.objects.create(
            school=instance.school,
            message=f"Session '{instance.session}' was {'created' if created else 'updated'}."
        )

@receiver(post_save, sender=Term)
def log_term_save(sender, instance, created, **kwargs):
    if instance.school:
        ActivityLog.objects.create(
            school=instance.school,
            message=f"Term '{instance}' was {'created' if created else 'updated'}."
        )


# =========================================================
#  SCHOOL CLASS (UPDATED WITH LEVEL CHOICES)
# =========================================================
class SchoolClass(models.Model):
    LEVEL_CHOICES = (
        ('F1', 'Form 1'),
        ('F2', 'Form 2'),
        ('F3', 'Form 3'),
        ('F4', 'Form 4'),
        ('F5', 'Form 5'),
        ('F6', 'Form 6'),
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50)          # e.g., "Form 1A"
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='F1')
    class_teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_lecturer': True}
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["school", "level", "is_active"], name="class_school_level_idx"),
        ]

# =========================================================
# FEE & PAYMENT MODELS
# =========================================================

FEE_STATUS_PENDING = "pending"
FEE_STATUS_PARTIAL = "partial"
FEE_STATUS_PAID = "paid"
FEE_STATUS_OVERDUE = "overdue"

FEE_STATUS_CHOICES = (
    (FEE_STATUS_PENDING, _("Pending")),
    (FEE_STATUS_PARTIAL, _("Partially Paid")),
    (FEE_STATUS_PAID, _("Paid")),
    (FEE_STATUS_OVERDUE, _("Overdue")),
)

PAYMENT_METHOD_CHOICES = (
    ("cash", _("Cash")),
    ("bank", _("Bank Transfer")),
    ("mobile_money", _("Mobile Money")),
    ("card", _("Card")),
    ("other", _("Other")),
)


class SchoolFee(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey("accounts.Student", on_delete=models.CASCADE, related_name="fees")
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=160, default=_("Tuition fees"))
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=FEE_STATUS_CHOICES, default=FEE_STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["school", "status", "due_date"], name="fee_school_status_due_idx"),
            models.Index(fields=["school", "student"], name="fee_school_student_idx"),
            models.Index(fields=["school", "session", "term"], name="fee_school_period_idx"),
        ]

    def __str__(self):
        return f"{self.student} - {self.description}"

    def save(self, *args, **kwargs):
        if not self.school_id:
            self.school = self.student.student.school
        super().save(*args, **kwargs)

    @property
    def total_paid(self):
        return sum(payment.amount for payment in self.payments.all())

    @property
    def balance(self):
        return self.amount_due - self.discount - self.total_paid

    def refresh_status(self, save=True):
        if self.balance <= 0:
            self.status = FEE_STATUS_PAID
        elif self.total_paid > 0:
            self.status = FEE_STATUS_PARTIAL
        elif self.due_date and self.due_date < timezone.localdate():
            self.status = FEE_STATUS_OVERDUE
        else:
            self.status = FEE_STATUS_PENDING
        if save:
            self.save(update_fields=["status", "updated_at"])
        return self.status


class FeePayment(models.Model):
    fee = models.ForeignKey(SchoolFee, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="cash")
    reference = models.CharField(max_length=120, blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"is_staff": True},
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-paid_on", "-id")
        indexes = [
            models.Index(fields=["fee", "-paid_on"], name="payment_fee_paid_idx"),
            models.Index(fields=["received_by", "-paid_on"], name="payment_receiver_idx"),
        ]

    def __str__(self):
        return f"{self.fee} - {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.fee.refresh_status()

    def delete(self, *args, **kwargs):
        fee = self.fee
        super().delete(*args, **kwargs)
        fee.refresh_status()


# =========================================================
# 💰 EXPENSES MODEL
# =========================================================

EXPENSE_CATEGORY_CHOICES = (
    ("salaries", _("Salaries & Wages")),
    ("utilities", _("Utilities (Water, Electricity, Internet)")),
    ("maintenance", _("Maintenance & Repairs")),
    ("supplies", _("School Supplies & Equipment")),
    ("transport", _("Transportation")),
    ("food", _("Food & Catering")),
    ("events", _("Events & Activities")),
    ("marketing", _("Marketing & Advertising")),
    ("insurance", _("Insurance")),
    ("rent", _("Rent & Leasing")),
    ("technology", _("Technology & Software")),
    ("professional", _("Professional Services (Legal, Audit)")),
    ("other", _("Other Expenses")),
)


class Expense(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="expenses")
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=EXPENSE_CATEGORY_CHOICES, default="other")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    expense_date = models.DateField(default=timezone.localdate)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    receipt_number = models.CharField(max_length=120, blank=True, help_text=_("Optional receipt or invoice reference"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-expense_date", "-created_at")
        indexes = [
            models.Index(fields=["school", "-expense_date"], name="expense_school_date_idx"),
            models.Index(fields=["school", "category"], name="expense_school_category_idx"),
        ]

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.expense_date})"


@receiver(post_save, sender=Expense)
def log_expense_save(sender, instance, created, **kwargs):
    if instance.school:
        ActivityLog.objects.create(
            school=instance.school,
            message=f"Expense '{instance.title}' ({instance.amount}) was {'recorded' if created else 'updated'}."
        )

@receiver(post_delete, sender=Expense)
def log_expense_delete(sender, instance, **kwargs):
    if instance.school:
        ActivityLog.objects.create(
            school=instance.school,
            message=f"Expense '{instance.title}' ({instance.amount}) was deleted."
        )


# =========================================================
# ATTENDANCE, EXAM, MARK, TIMETABLE
# =========================================================

ATTENDANCE_PRESENT = "present"
ATTENDANCE_ABSENT = "absent"
ATTENDANCE_LATE = "late"
ATTENDANCE_EXCUSED = "excused"

ATTENDANCE_STATUS_CHOICES = (
    (ATTENDANCE_PRESENT, _("Present")),
    (ATTENDANCE_ABSENT, _("Absent")),
    (ATTENDANCE_LATE, _("Late")),
    (ATTENDANCE_EXCUSED, _("Excused")),
)

EXAM_DRAFT = "draft"
EXAM_SCHEDULED = "scheduled"
EXAM_IN_PROGRESS = "in_progress"
EXAM_COMPLETED = "completed"
EXAM_PUBLISHED = "published"

EXAM_STATUS_CHOICES = (
    (EXAM_DRAFT, _("Draft")),
    (EXAM_SCHEDULED, _("Scheduled")),
    (EXAM_IN_PROGRESS, _("In Progress")),
    (EXAM_COMPLETED, _("Completed")),
    (EXAM_PUBLISHED, _("Published")),
)


class Exam(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, null=True, blank=True, related_name="exams")
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=EXAM_STATUS_CHOICES, default=EXAM_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.school_class})"

    class Meta:
        indexes = [
            models.Index(fields=["school", "status"], name="exam_school_status_idx"),
            models.Index(fields=["school", "school_class"], name="exam_school_class_idx"),
            models.Index(fields=["school", "starts_on"], name="exam_school_starts_idx"),
        ]


class ExamSchedule(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="schedule_entries")
    subject = models.ForeignKey("course.Subject", on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=120, blank=True)
    invigilator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={"is_lecturer": True})

    class Meta:
        indexes = [
            models.Index(fields=["exam", "date"], name="schedule_exam_date_idx"),
        ]

    def __str__(self):
        return f"{self.subject} - {self.date}"


# =========================================================
# MARK ENTRY MODELS
# =========================================================

class MarkEntry(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey("accounts.Student", on_delete=models.CASCADE)
    subject = models.ForeignKey("course.Subject", on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True, blank=True)
    continuous_assessment = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    exam_mark = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.subject}"


DAY_CHOICES = (
    ("monday", _("Monday")),
    ("tuesday", _("Tuesday")),
    ("wednesday", _("Wednesday")),
    ("thursday", _("Thursday")),
    ("friday", _("Friday")),
    ("saturday", _("Saturday")),
    ("sunday", _("Sunday")),
)


class TimetableEntry(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="timetable_entries")
    subject = models.ForeignKey("course.Subject", on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={"is_lecturer": True})
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("day", "start_time")
        indexes = [
            models.Index(fields=["school", "school_class", "day"], name="tt_school_class_day_idx"),
            models.Index(fields=["school", "teacher", "day"], name="tt_school_teacher_day_idx"),
        ]

    def __str__(self):
        return f"{self.school_class} - {self.subject} ({self.get_day_display()} {self.start_time}-{self.end_time})"


# =========================================================
# ATTENDANCE RECORD
# =========================================================

class AttendanceRecord(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey("accounts.Student", on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey("course.Subject", on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ("student", "school_class", "subject", "date")
        indexes = [
            models.Index(fields=["school", "date"], name="attendance_school_date_idx"),
            models.Index(fields=["school", "student", "date"], name="attendance_student_date_idx"),
        ]

    def __str__(self):
        return f"{self.student} - {self.status} on {self.date}"
