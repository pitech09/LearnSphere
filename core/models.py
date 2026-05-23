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

SCHOOL_PLAN_CHOICES = (
    (SCHOOL_PLAN_STARTER, _("Starter")),
    (SCHOOL_PLAN_GROWTH, _("Growth")),
    (SCHOOL_PLAN_ENTERPRISE, _("Enterprise")),
)


class School(models.Model):
    name = models.CharField(max_length=180)
    slug = models.SlugField(unique=True, blank=True)
    subdomain = models.SlugField(max_length=80, unique=True, blank=True, null=True)
    registration_number = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=60, blank=True)
    address = models.CharField(max_length=220, blank=True)
    status = models.CharField(max_length=20, choices=SCHOOL_STATUS_CHOICES, default=SCHOOL_STATUS_TRIAL)
    plan = models.CharField(max_length=20, choices=SCHOOL_PLAN_CHOICES, default=SCHOOL_PLAN_STARTER)
    trial_ends_on = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 2
            while School.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if not self.subdomain:
            self.subdomain = self.slug
        super().save(*args, **kwargs)

POST_NEWS = "news"
POST_EVENT = "event"

POST_CHOICES = (
    (POST_NEWS, _("News")),
    (POST_EVENT, _("Event")),
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NewsAndEventsManager()

    def __str__(self):
        return self.title


# =========================================================
# 📅 SESSION (ACADEMIC YEAR)
# =========================================================

class Session(models.Model):
    """
    Represents academic year (e.g. 2026)
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    session = models.CharField(max_length=200)
    is_current = models.BooleanField(default=False)
    next_session_begins = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.session

    class Meta:
        unique_together = ("school", "session")


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


# =========================================================
# 🧾 ACTIVITY LOG
# =========================================================

class ActivityLog(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message[:60]


# =========================================================
# 👤 USER SYSTEM
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
# 🔔 SIGNALS
# =========================================================

@receiver(post_save, sender=NewsAndEvents)
def log_news_save(sender, instance, created, **kwargs):
    ActivityLog.objects.create(
        message=f"News/Event '{instance.title}' was {'created' if created else 'updated'}."
    )


@receiver(post_delete, sender=NewsAndEvents)
def log_news_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        message=f"News/Event '{instance.title}' was deleted."
    )


@receiver(post_save, sender=Session)
def log_session_save(sender, instance, created, **kwargs):
    ActivityLog.objects.create(
        message=f"Session '{instance.session}' was {'created' if created else 'updated'}."
    )


@receiver(post_save, sender=Term)
def log_term_save(sender, instance, created, **kwargs):
    ActivityLog.objects.create(
        message=f"Term '{instance}' was {'created' if created else 'updated'}."
    )

# =========================================================
#  SCHOOL CLASS (FORM 1A, FORM 2B, etc.)
# =========================================================
class SchoolClass(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50)  # e.g. F1A, F2B
    level = models.CharField(max_length=10)  # e.g. F1, F2, F3
    class_teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'is_lecturer': True}
    )
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.name

    class Meta:
        unique_together = ("school", "name")


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

DAY_CHOICES = (
    ("monday", _("Monday")),
    ("tuesday", _("Tuesday")),
    ("wednesday", _("Wednesday")),
    ("thursday", _("Thursday")),
    ("friday", _("Friday")),
    ("saturday", _("Saturday")),
    ("sunday", _("Sunday")),
)

MARK_STATUS_DRAFT = "draft"
MARK_STATUS_APPROVED = "approved"
MARK_STATUS_PUBLISHED = "published"

MARK_STATUS_CHOICES = (
    (MARK_STATUS_DRAFT, _("Draft")),
    (MARK_STATUS_APPROVED, _("Approved")),
    (MARK_STATUS_PUBLISHED, _("Published")),
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

    def __str__(self):
        return f"{self.fee} - {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.fee.refresh_status()

    def delete(self, *args, **kwargs):
        fee = self.fee
        super().delete(*args, **kwargs)
        fee.refresh_status()


class AttendanceRecord(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey("accounts.Student", on_delete=models.CASCADE, related_name="attendance_records")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="attendance_records")
    subject = models.ForeignKey("course.Subject", on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS_CHOICES, default=ATTENDANCE_PRESENT)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"is_lecturer": True},
    )
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("-date", "school_class__name", "student__student__last_name")
        unique_together = ("student", "school_class", "subject", "date")

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.school_id:
            self.school = self.student.student.school
        super().save(*args, **kwargs)


class Exam(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=160)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="exams")
    starts_on = models.DateField()
    ends_on = models.DateField()
    status = models.CharField(max_length=20, choices=EXAM_STATUS_CHOICES, default=EXAM_DRAFT)
    results_published = models.BooleanField(default=False)

    class Meta:
        ordering = ("-starts_on", "name")

    def __str__(self):
        return f"{self.name} - {self.school_class}"

    def save(self, *args, **kwargs):
        if not self.school_id:
            self.school = self.school_class.school
        super().save(*args, **kwargs)


class ExamSchedule(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="schedule_entries")
    subject = models.ForeignKey("course.Subject", on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=120, blank=True)
    invigilator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"is_lecturer": True},
    )

    class Meta:
        ordering = ("date", "start_time")
        unique_together = ("exam", "subject")

    def __str__(self):
        return f"{self.exam} - {self.subject}"


class MarkEntry(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey("accounts.Student", on_delete=models.CASCADE, related_name="mark_entries")
    subject = models.ForeignKey("course.Subject", on_delete=models.CASCADE, related_name="mark_entries")
    exam = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True, blank=True, related_name="mark_entries")
    continuous_assessment = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    exam_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    final_mark = models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)
    status = models.CharField(max_length=20, choices=MARK_STATUS_CHOICES, default=MARK_STATUS_DRAFT)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"is_lecturer": True},
    )
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("student__student__last_name", "subject__title")
        unique_together = ("student", "subject", "exam")

    def __str__(self):
        return f"{self.student} - {self.subject} ({self.final_mark})"

    def save(self, *args, **kwargs):
        if not self.school_id:
            self.school = self.student.student.school
        self.final_mark = (
            self.continuous_assessment * Decimal("0.40")
            + self.exam_mark * Decimal("0.60")
        )
        if self.status in {MARK_STATUS_APPROVED, MARK_STATUS_PUBLISHED} and not self.processed_at:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)


class TimetableEntry(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="timetable_entries")
    subject = models.ForeignKey("course.Subject", on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"is_lecturer": True},
    )
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("school_class__name", "day", "start_time")
        unique_together = ("school_class", "day", "start_time")

    def __str__(self):
        return f"{self.school_class} - {self.day} - {self.subject}"

    def save(self, *args, **kwargs):
        if not self.school_id:
            self.school = self.school_class.school
        super().save(*args, **kwargs)




   
