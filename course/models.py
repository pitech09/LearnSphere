from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save, post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from accounts.models import User
from core.models import ActivityLog, Session
from core.utils import unique_slug_generator


# =========================================================
# COURSE MANAGER
# =========================================================
class CourseManager(models.Manager):
    def search(self, query=None):
        queryset = self.get_queryset()
        if query:
            or_lookup = (
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(code__icontains=query)
                | Q(slug__icontains=query)
            )
            queryset = queryset.filter(or_lookup).distinct()
        return queryset


# =========================================================
# COURSE (HIGH SCHOOL VERSION)
# =========================================================
class Subject(models.Model):
    slug = models.SlugField(unique=True, blank=True)
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=200, unique=True)
    summary = models.TextField(max_length=200, blank=True)

    class_assigned = models.ForeignKey('core.SchoolClass', on_delete=models.CASCADE, null=True, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    objects = CourseManager()

    def __str__(self):
        return f"{self.title} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.code}")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"slug": self.slug})

    @property
    def is_current(self):
        current = Session.objects.filter(is_current=True).first()
        return bool(current) 

# =========================================================
# SIGNALS
# =========================================================
@receiver(pre_save, sender=Subject)
def subject_pre_save_receiver(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)


@receiver(post_save, sender=Subject)
def log_subject_save(sender, instance, created, **kwargs):
    verb = "created" if created else "updated"
    ActivityLog.objects.create(
        message=_(f"The subject '{instance}' has been {verb}.")
    )


@receiver(post_delete, sender=Subject)
def log_subject_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        message=_(f"The subject '{instance}' has been deleted.")
    )


class SubjectAllocation(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="allocated_teacher",
    )

    subjects = models.ManyToManyField(
        "Subject",
        related_name="allocated_subjects"
    )

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.teacher.get_full_name() or self.teacher.username

    def get_absolute_url(self):
        return reverse("edit_allocated_subject", kwargs={"pk": self.pk})

# =========================================================
# UPLOADS
# =========================================================
class Upload(models.Model):
    title = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    file = models.FileField(
        upload_to="course_files/",
        validators=[
            FileExtensionValidator([
                "pdf", "docx", "doc", "xls", "xlsx",
                "ppt", "pptx", "zip", "rar", "7zip"
            ])
        ],
    )

    updated_date = models.DateTimeField(auto_now=True)
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


@receiver(post_save, sender=Upload)
def log_upload_save(sender, instance, created, **kwargs):
    action = "uploaded" if created else "updated"
    ActivityLog.objects.create(
        message=_(f"The file '{instance.title}' has been {action} in '{instance.course}'.")
    )


@receiver(post_delete, sender=Upload)
def log_upload_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        message=_(f"The file '{instance.title}' was deleted from '{instance.course}'.")
    )


# =========================================================
# VIDEO UPLOAD
# =========================================================
class UploadVideo(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    video = models.FileField(
        upload_to="course_videos/",
        validators=[
            FileExtensionValidator(
                ["mp4", "mkv", "wmv", "3gp", "f4v", "avi", "mp3"]
            )
        ],
    )

    summary = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "video_single",
            kwargs={"slug": self.subject.slug, "video_slug": self.slug},
        )


@receiver(pre_save, sender=UploadVideo)
def video_pre_save_receiver(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)


@receiver(post_save, sender=UploadVideo)
def log_uploadvideo_save(sender, instance, created, **kwargs):
    action = "uploaded" if created else "updated"
    ActivityLog.objects.create(
        message=_(f"The video '{instance.title}' has been {action} in '{instance.subject}'.")
    )

@receiver(post_delete, sender=UploadVideo)
def log_uploadvideo_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        message=_(f"The video '{instance.title}' was deleted from '{instance.subject}'.")
    )

# =========================================================
# COURSE OFFER (optional admin grouping)
# =========================================================
class CourseOffer(models.Model):
    dep_head = models.ForeignKey("accounts.DepartmentHead", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.dep_head)