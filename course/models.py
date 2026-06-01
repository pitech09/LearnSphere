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
# SUBJECT (COURSE)
# =========================================================
class Subject(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, null=True, blank=True)
    slug = models.SlugField(blank=True)   # unique per school+class (enforced by constraint)
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=200)
    summary = models.TextField(max_length=200, blank=True)

    class_assigned = models.ForeignKey('core.SchoolClass', on_delete=models.CASCADE, null=True, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Elective subject flag - if True, students can optionally add this subject
    is_electable = models.BooleanField(
        default=False,
        verbose_name=_("Electable Subject"),
        help_text=_("If checked, students can optionally add this subject to their class subjects")
    )

    objects = CourseManager()

    class Meta:
        #unique_together = ("school", "class_assigned", "code")
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'class_assigned', 'slug'],
                name='unique_subject_slug_per_class'
            )
        ]
        indexes = [
            models.Index(fields=["school", "class_assigned"], name="subject_school_class_idx"),
            models.Index(fields=["school", "teacher"], name="subject_school_teacher_idx"),
            models.Index(fields=["school", "code"], name="subject_school_code_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.school_id:
            if self.class_assigned_id:
                self.school = self.class_assigned.school
            elif self.teacher_id:
                self.school = self.teacher.school

        if not self.slug:
            base_slug = slugify(f"{self.title}-{self.code}")
            slug = base_slug
            counter = 2
            while Subject.objects.filter(
                school=self.school,
                class_assigned=self.class_assigned,
                slug=slug
            ).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={
            "class_id": self.class_assigned.id,
            "subject_slug": self.slug
        }) 

    def __str__(self):
        return f"{self.title} ({self.code})"


# =========================================================
# SIGNALS FOR SUBJECT
# =========================================================
@receiver(post_save, sender=Subject)
def log_subject_save(sender, instance, created, **kwargs):
    verb = "created" if created else "updated"
    if instance.school:   # safety guard
        ActivityLog.objects.create(
            school=instance.school,
            message=_(f"The subject '{instance}' has been {verb}.")
        )

@receiver(post_delete, sender=Subject)
def log_subject_delete(sender, instance, **kwargs):
    if instance.school:
        ActivityLog.objects.create(
            school=instance.school,
            message=_(f"The subject '{instance}' has been deleted.")
        )


# =========================================================
# STUDENT ELECTED SUBJECT (OPTIONAL SUBJECTS CHOSEN BY STUDENTS)
# =========================================================
class StudentElectedSubject(models.Model):
    """
    Tracks elective subjects that a student has chosen to add to their class subjects.
    """
    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        related_name="elected_subjects"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="elected_by_students"
    )
    elected_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("student", "subject")
        ordering = ["subject__title"]
        indexes = [
            models.Index(fields=["student", "subject"], name="elected_student_subject_idx"),
        ]
    
    def __str__(self):
        return f"{self.student.student.get_full_name()} - {self.subject.title}"


# =========================================================
# SUBJECT ALLOCATION
# =========================================================
class SubjectAllocation(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="allocated_teacher",
    )
    subjects = models.ManyToManyField("Subject", related_name="allocated_subjects")
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.teacher.get_full_name() or self.teacher.username

    def get_absolute_url(self):
        return reverse("edit_allocated_subject", kwargs={"pk": self.pk})

    class Meta:
        indexes = [
            models.Index(fields=["teacher", "session"], name="alloc_teacher_session_idx"),
        ]


# =========================================================
# FILE UPLOADS
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

    class Meta:
        indexes = [
            models.Index(fields=["subject", "-upload_time"], name="upload_subject_time_idx"),
        ]


@receiver(post_save, sender=Upload)
def log_upload_save(sender, instance, created, **kwargs):
    action = "uploaded" if created else "updated"
    if instance.subject and instance.subject.school:
        ActivityLog.objects.create(
            school=instance.subject.school,
            message=_(f"The file '{instance.title}' has been {action} in '{instance.subject}'.")
        )

@receiver(post_delete, sender=Upload)
def log_upload_delete(sender, instance, **kwargs):
    if instance.subject and instance.subject.school:
        ActivityLog.objects.create(
            school=instance.subject.school,
            message=_(f"The file '{instance.title}' was deleted from '{instance.subject}'.")
        )


# =========================================================
# VIDEO UPLOADS
# =========================================================
class UploadVideo(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)   # keep unique globally, but may change later
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
        return reverse("video_single", kwargs={
            "class_id": self.subject.class_assigned.id,
            "subject_slug": self.subject.slug,
            "video_slug": self.slug
        })
    class Meta:
        indexes = [
            models.Index(fields=["subject", "-timestamp"], name="video_subject_time_idx"),
        ]


@receiver(pre_save, sender=UploadVideo)
def video_pre_save_receiver(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)

@receiver(post_save, sender=UploadVideo)
def log_uploadvideo_save(sender, instance, created, **kwargs):
    action = "uploaded" if created else "updated"
    if instance.subject and instance.subject.school:
        ActivityLog.objects.create(
            school=instance.subject.school,
            message=_(f"The video '{instance.title}' has been {action} in '{instance.subject}'.")
        )

@receiver(post_delete, sender=UploadVideo)
def log_uploadvideo_delete(sender, instance, **kwargs):
    if instance.subject and instance.subject.school:
        ActivityLog.objects.create(
            school=instance.subject.school,
            message=_(f"The video '{instance.title}' was deleted from '{instance.subject}'.")
        )


# =========================================================
# COURSE OFFER (optional)
# =========================================================
class CourseOffer(models.Model):
    dep_head = models.ForeignKey("accounts.DepartmentHead", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.dep_head)