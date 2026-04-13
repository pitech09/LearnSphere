from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, UserManager
from django.urls import reverse

from accounts.models import User


# =========================================================
#  NEWS & EVENTS
# =========================================================

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
    session = models.CharField(max_length=200, unique=True)
    is_current = models.BooleanField(default=False)
    next_session_begins = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.session


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
    name = models.CharField(max_length=50, unique=True)  # e.g. F1A, F2B
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




   