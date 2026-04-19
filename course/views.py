from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django_filters.views import FilterView
from core.models import Term
from core.models import SchoolClass

from accounts.decorators import lecturer_required, student_required
from accounts.models import Student
from course.forms import (
    UploadFormFile,
    UploadFormVideo,
)
from course.models import (
    Subject,
    SubjectAllocation,
    Upload,
    UploadVideo,
)
from .forms import AssignClassForm, SubjectAddForm
from result.models import TakenCourse


# ########################################################
# Course Views
# ########################################################

@login_required
def course_single(request, slug):
    course = get_object_or_404(Subject, slug=slug)

    # FIX: course → subject
    files = Upload.objects.filter(subject=course)
    videos = UploadVideo.objects.filter(subject=course)

    # FIX: courses → subjects
    lecturers = SubjectAllocation.objects.filter(subjects=course)

    return render(
        request,
        "course/course_single.html",
        {
            "title": course.title,
            "course": course,
            "files": files,
            "videos": videos,
            "lecturers": lecturers,
            "media_url": settings.MEDIA_URL,
        },
    )


@login_required
@lecturer_required
def subject_add(request):
    if request.method == "POST":
        form = SubjectAddForm(request.POST)

        if form.is_valid():
            subject = form.save()

            messages.success(
                request,
                f"{subject.title} ({subject.code}) has been created."
            )
            return redirect("subject_list")

        messages.error(request, "Correct the error(s) below.")
    else:
        form = SubjectAddForm()

    return render(
        request,
        "core/subject_form.html",
        {
            "title": "Add Subject",
            "form": form,
        },
    )


@login_required
@lecturer_required
def course_edit(request, slug):
    course = get_object_or_404(Subject, slug=slug)
    if request.method == "POST":
        form = SubjectAddForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(
                request, f"{course.title} ({course.code}) has been updated."
            )
            return redirect("program_detail", pk=course.program.pk)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = SubjectAddForm(instance=course)
    return render(
        request, "course/course_add.html", {"title": "Edit Course", "form": form}
    )


@login_required
@lecturer_required
def subject_delete(request, slug):
    subject = get_object_or_404(Subject, slug=slug)
    title = subject.title
    subject.delete()
    messages.success(request, f"Subject {title} has been deleted.")
    return redirect("subject_list")


# ########################################################
# Course Allocation Views
# ########################################################

@login_required
@lecturer_required
def deallocate_course(request, pk):
    allocation = get_object_or_404(SubjectAllocation, pk=pk)
    allocation.delete()
    messages.success(request, "Successfully deallocated subjects.")
    return redirect("course_allocation_view")


# ########################################################
# File Upload Views
# ########################################################

@login_required
@lecturer_required
def handle_file_upload(request, slug):
    course = get_object_or_404(Subject, slug=slug)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)

            # FIX: course → subject
            upload.subject = course

            upload.save()
            messages.success(request, f"{upload.title} has been uploaded.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormFile()

    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "File Upload", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_edit(request, slug, file_id):
    course = get_object_or_404(Subject, slug=slug)
    upload = get_object_or_404(Upload, pk=file_id)

    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES, instance=upload)
        if form.is_valid():
            upload = form.save()
            messages.success(request, f"{upload.title} has been updated.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormFile(instance=upload)

    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "Edit File", "form": form, "course": course},
    )


@login_required
@lecturer_required
def subject_add_view(request):
    if request.method == "POST":
        form = SubjectAddForm(request.POST)

        if form.is_valid():
            subject = form.save()

            messages.success(
                request,
                f"{subject.title} ({subject.code}) has been created."
            )
            return redirect("subject_list")

        messages.error(request, "Correct the error(s) below.")
    else:
        form = SubjectAddForm()

    return render(
        request,
        "core/subject_form.html",
        {
            "title": "Add Subject",
            "form": form,
        },
    )


@login_required
@lecturer_required
def subject_update_view(request, pk):
    obj = get_object_or_404(Subject, pk=pk)
    form = SubjectAddForm(request.POST or None, instance=obj)

    if form.is_valid():
        form.save()
        messages.success(request, "Subject updated successfully")
        return redirect("subject_list")

    return render(request, "core/subject_form.html", {"form": form})


@login_required
@lecturer_required
def subject_delete_view(request, pk):
    obj = get_object_or_404(Subject, pk=pk)

    if request.method == "POST":
        obj.delete()
        messages.success(request, "Subject deleted")
        return redirect("subject_list")

    return render(request, "core/confirm_delete.html", {"object": obj})


@login_required
@lecturer_required
def handle_file_delete(request, slug, file_id):
    upload = get_object_or_404(Upload, pk=file_id)
    title = upload.title
    upload.delete()
    messages.success(request, f"{title} has been deleted.")
    return redirect("course_detail", slug=slug)


# ########################################################
# Video Upload Views
# ########################################################

@login_required
@lecturer_required
def handle_video_upload(request, slug):
    course = get_object_or_404(Subject, slug=slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)

            # FIX: course → subject
            video.subject = course

            video.save()
            messages.success(request, f"{video.title} has been uploaded.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormVideo()

    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Video Upload", "form": form, "course": course},
    )


@login_required
def handle_video_single(request, slug, video_slug):
    course = get_object_or_404(Subject, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)

    return render(
        request,
        "upload/video_single.html",
        {"video": video, "course": course},
    )


@login_required
@lecturer_required
def handle_video_edit(request, slug, video_slug):
    course = get_object_or_404(Subject, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)

    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES, instance=video)
        if form.is_valid():
            video = form.save()
            messages.success(request, f"{video.title} has been updated.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormVideo(instance=video)

    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Edit Video", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_video_delete(request, slug, video_slug):
    video = get_object_or_404(UploadVideo, slug=video_slug)
    title = video.title
    video.delete()
    messages.success(request, f"{title} has been deleted.")
    return redirect("course_detail", slug=slug)


# ########################################################
# Course Registration Views
# ########################################################

@login_required
@student_required
def course_registration(request):

    student = get_object_or_404(Student, student__id=request.user.id)

    if request.method == "POST":
        course_ids = request.POST.getlist("course_ids")

        for cid in course_ids:
            try:
                course = Subject.objects.get(pk=cid)

                TakenCourse.objects.get_or_create(
                    student=student,
                    course=course
                )

            except Subject.DoesNotExist:
                pass

        messages.success(request, "Courses registered successfully!")
        return redirect("course_registration")

    current_term = Term.objects.filter(is_current=True).first()

    if not current_term:
        messages.error(request, "No active term found.")
        return render(request, "course/course_registration.html", {})

    taken_ids = TakenCourse.objects.filter(
        student__student__id=request.user.id
    ).values_list("course_id", flat=True)

    courses = Subject.objects.filter(
        semester=current_term.term
    ).exclude(id__in=taken_ids)

    registered_courses = Subject.objects.filter(id__in=taken_ids)

    return render(request, "course/course_registration.html", {
        "student": student,
        "current_term": current_term,
        "courses": courses,
        "registered_courses": registered_courses,
    })


@login_required
@student_required
def course_drop(request):
    if request.method == "POST":
        student = get_object_or_404(Student, student__pk=request.user.id)
        course_ids = request.POST.getlist("course_ids")

        for course_id in course_ids:
            course = get_object_or_404(Subject, pk=course_id)
            TakenCourse.objects.filter(student=student, course=course).delete()

        messages.success(request, "Courses dropped successfully!")
        return redirect("course_registration")


# ########################################################
# User Course List View
# ########################################################

@login_required
def user_course_list(request):

    #  STUDENT VIEW
    if request.user.is_student:

        student = get_object_or_404(Student, student=request.user)

        if not student.student_class:
            return render(request, "course/user_course_list.html", {
                "courses": [],
                "student": student,
                "message": "No class assigned yet"
            })

        courses = Subject.objects.filter(
            class_assigned=student.student_class
        )

        return render(request, "course/user_course_list.html", {
            "courses": courses,
            "student": student,
        })

    #  LECTURER VIEW
    if request.user.is_lecturer:

        courses = Subject.objects.filter(
            teacher=request.user
        )

        return render(request, "course/user_course_list.html", {
            "courses": courses,
        })

    return render(request, "course/user_course_list.html")

@login_required
def assign_class_view(request, student_id):

    student = get_object_or_404(Student, id=student_id)

    form = AssignClassForm(request.POST or None, instance=student)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("student_list")  # or wherever your list page is

    return render(request, "course/assign_class.html", {
        "form": form,
        "student": student
    })