from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from accounts.decorators import admin_required, lecturer_required
from accounts.models import User, Student
from course.forms import SubjectAddForm
from course.models import Subject, SubjectAllocation

from .forms import SessionForm, NewsAndEventsForm, SubjectForm
from .models import NewsAndEvents, ActivityLog, Session, SchoolClass


# =========================================================
# NEWS & EVENTS
# =========================================================
@login_required
def home_view(request):
    items = NewsAndEvents.objects.all().order_by("-updated_at")

    return render(request, "core/index.html", {
        "title": "News & Events",
        "items": items,
    })


# =========================================================
# DASHBOARD
# =========================================================
@login_required
@admin_required
def dashboard_view(request):
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]

    gender_count = Student.get_gender_count()

    return render(request, "core/dashboard.html", {
        "student_count": User.objects.get_student_count(),
        "lecturer_count": User.objects.get_lecturer_count(),
        "superuser_count": User.objects.get_superuser_count(),
        "males_count": gender_count.get("M", 0),
        "females_count": gender_count.get("F", 0),
        "logs": logs,
    })


# =========================================================
# NEWS POSTING
# =========================================================
@login_required
def post_add(request):
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST)

        if form.is_valid():
            post = form.save()
            messages.success(request, f"{post.title} has been created.")
            return redirect("home")

        messages.error(request, "Please correct the error(s).")

    else:
        form = NewsAndEventsForm()

    return render(request, "core/post_add.html", {
        "title": "Add Post",
        "form": form
    })


@login_required
@lecturer_required
def edit_post(request, pk):
    post = get_object_or_404(NewsAndEvents, pk=pk)

    if request.method == "POST":
        form = NewsAndEventsForm(request.POST, instance=post)

        if form.is_valid():
            form.save()
            messages.success(request, "Post updated.")
            return redirect("home")

    else:
        form = NewsAndEventsForm(instance=post)

    return render(request, "core/post_add.html", {
        "title": "Edit Post",
        "form": form
    })


@login_required
@lecturer_required
def delete_post(request, pk):
    post = get_object_or_404(NewsAndEvents, pk=pk)
    title = post.title
    post.delete()

    messages.success(request, f"{title} deleted.")
    return redirect("home")


# =========================================================
# SESSION MANAGEMENT (NO SEMESTER ANYMORE)
# =========================================================
@login_required
@lecturer_required
def session_list_view(request):
    sessions = Session.objects.all().order_by("-is_current", "-session")
    for session in sessions:
        print(f"Session: {session.session}, Is Current: {session.is_current}")
    return render(request, "core/session_list.html", {
        "sessions": sessions
    })


@login_required
@lecturer_required
def session_add_view(request):
    if request.method == "POST":
        form = SessionForm(request.POST)

        if form.is_valid():
            if form.cleaned_data.get("is_current"):
                print(f"Setting current session...{form.cleaned_data.get('is_current')}")
                Session.objects.filter(is_current=True).update(is_current=False)

            form.save()
            messages.success(request, "Session added.")
            return redirect("session_list")
    else:
        form = SessionForm()

    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_update_view(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if request.method == "POST":
        form = SessionForm(request.POST, instance=session)

        if form.is_valid():
            if form.cleaned_data.get("is_current"):
                Session.objects.filter(is_current=True).update(is_current=False)

            form.save()
            messages.success(request, "Session updated.")
            return redirect("session_list")

    else:
        form = SessionForm(instance=session)

    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_delete_view(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if session.is_current:
        messages.error(request, "You cannot delete the current session.")
    else:
        session.delete()
        messages.success(request, "Session deleted.")

    return redirect("session_list")

@login_required
@lecturer_required
def subject_list_view(request):
    subjects = Subject.objects.all()
    return render(request, "core/subject_list.html", {"subjects": subjects})


@login_required
@lecturer_required
def subject_add_view(request):
    if request.method == "POST":
        form = SubjectAddForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Subject added.")
            return redirect("subject_list_view")
    else:
        form = SubjectAddForm()

    return render(request, "core/subject_form.html", {"form": form})

@login_required
@lecturer_required
def subject_update_view(request, pk):
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == "POST":
        form = SubjectAddForm(request.POST, instance=subject)

        if form.is_valid():
            form.save()
            messages.success(request, "Subject updated.")
            return redirect("subject_list_view")

    else:
        form = SubjectAddForm(instance=subject)

    return render(request, "core/subject_form.html", {"form": form})

@login_required
@lecturer_required
def subject_delete_view(request, pk):
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == "POST":
        subject.delete()
        messages.success(request, "Subject deleted.")
        return redirect("subject_list_view")

    return render(request, "core/confirm_delete.html", {"object": subject})

from .models import SchoolClass
from .forms import (
    SchoolClassForm
)

@login_required
@lecturer_required
def class_list_view(request):
    classes = SchoolClass.objects.all()
    return render(request, "core/class_list.html", {"classes": classes})


@login_required
@lecturer_required
def class_add_view(request):
    form = SchoolClassForm(request.POST or None)

    if request.method == "POST":
            print(" POST DATA:", request.POST)

            if form.is_valid():
                print(" VALID FORM")
                form.save()
            else:
                print(" FORM ERRORS:", form.errors)

    return render(request, "core/class_form.html", {"form": form})

@login_required
@lecturer_required
def class_update_view(request, pk):
    obj = get_object_or_404(SchoolClass, pk=pk)
    form = SchoolClassForm(request.POST or None, instance=obj)

    if form.is_valid():
        form.save()
        messages.success(request, "Class updated successfully")
        return redirect("class_list")

    return render(request, "core/class_form.html", {"form": form})


@login_required
@lecturer_required
def class_delete_view(request, pk):
    obj = get_object_or_404(SchoolClass, pk=pk)

    if request.method == "POST":
        obj.delete()
        messages.success(request, "Class deleted")
        return redirect("class_list")

    return render(request, "core/confirm_delete.html", {"object": obj})


