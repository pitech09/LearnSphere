from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
<<<<<<< HEAD
from django.db.models import Avg

from accounts.decorators import admin_required, lecturer_required
from accounts.models import Parent, TeacherProfile, User, Student
=======

from accounts.decorators import admin_required, lecturer_required
from accounts.models import User, Student
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
from course.forms import SubjectAddForm
from course.models import Subject, SubjectAllocation

from .forms import SessionForm, NewsAndEventsForm, SubjectForm
<<<<<<< HEAD
from .models import (
    ATTENDANCE_PRESENT,
    AttendanceRecord,
    Exam,
    MarkEntry,
    NewsAndEvents,
    ActivityLog,
    SchoolFee,
    Session,
    SchoolClass,
    TimetableEntry,
)
=======
from .models import NewsAndEvents, ActivityLog, Session, SchoolClass
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e


# =========================================================
# NEWS & EVENTS
# =========================================================
@login_required
def home_view(request):
    items = NewsAndEvents.objects.all().order_by("-updated_at")
<<<<<<< HEAD
    if request.user.school:
        items = items.filter(school=request.user.school)
=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e

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
<<<<<<< HEAD
    school = getattr(request.user, "school", None)
    school_filter = {"school": school} if school else {}
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]

    students = Student.objects.filter(student__school=school) if school else Student.objects.all()
    users = User.objects.filter(school=school) if school else User.objects.all()
    gender_count = {
        "M": students.filter(student__gender="M").count(),
        "F": students.filter(student__gender="F").count(),
    }
    attendance_total = AttendanceRecord.objects.filter(**school_filter).count()
    attendance_present = AttendanceRecord.objects.filter(status=ATTENDANCE_PRESENT, **school_filter).count()
    attendance_rate = round((attendance_present / attendance_total) * 100, 1) if attendance_total else 0

    fees = SchoolFee.objects.filter(**school_filter).prefetch_related("payments")
    outstanding_fees = sum(fee.balance for fee in fees)
    collected_fees = sum(fee.total_paid for fee in fees)
    average_mark = MarkEntry.objects.filter(**school_filter).aggregate(value=Avg("final_mark")).get("value") or 0
    upcoming_exams = Exam.objects.filter(**school_filter).exclude(status="completed").order_by("starts_on")[:5]

    return render(request, "core/dashboard.html", {
        "school": school,
        "student_count": users.filter(is_student=True).count(),
        "lecturer_count": users.filter(is_lecturer=True).count(),
        "teacher_profile_count": TeacherProfile.objects.filter(user__school=school).count() if school else TeacherProfile.objects.count(),
        "parent_count": Parent.objects.filter(user__school=school).count() if school else Parent.objects.count(),
        "superuser_count": users.filter(is_superuser=True).count(),
        "class_count": SchoolClass.objects.filter(is_active=True, **school_filter).count(),
        "timetable_count": TimetableEntry.objects.filter(is_active=True, **school_filter).count(),
        "exam_count": Exam.objects.filter(**school_filter).count(),
        "marks_count": MarkEntry.objects.filter(**school_filter).count(),
        "attendance_rate": attendance_rate,
        "outstanding_fees": outstanding_fees,
        "collected_fees": collected_fees,
        "average_mark": average_mark,
        "upcoming_exams": upcoming_exams,
=======
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]

    gender_count = Student.get_gender_count()

    return render(request, "core/dashboard.html", {
        "student_count": User.objects.get_student_count(),
        "lecturer_count": User.objects.get_lecturer_count(),
        "superuser_count": User.objects.get_superuser_count(),
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
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
<<<<<<< HEAD
    if request.user.school:
        subjects = subjects.filter(school=request.user.school)
=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
    return render(request, "core/subject_list.html", {"subjects": subjects})


@login_required
@lecturer_required
def subject_add_view(request):
    if request.method == "POST":
<<<<<<< HEAD
        form = SubjectAddForm(request.POST, school=request.user.school)

        if form.is_valid():
            subject = form.save(commit=False)
            subject.school = request.user.school
            subject.save()
            messages.success(request, "Subject added.")
            return redirect("subject_list_view")
    else:
        form = SubjectAddForm(school=request.user.school)
=======
        form = SubjectAddForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Subject added.")
            return redirect("subject_list_view")
    else:
        form = SubjectAddForm()
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e

    return render(request, "core/subject_form.html", {"form": form})

@login_required
@lecturer_required
def subject_update_view(request, pk):
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == "POST":
<<<<<<< HEAD
        form = SubjectAddForm(request.POST, instance=subject, school=request.user.school)
=======
        form = SubjectAddForm(request.POST, instance=subject)
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e

        if form.is_valid():
            form.save()
            messages.success(request, "Subject updated.")
            return redirect("subject_list_view")

    else:
<<<<<<< HEAD
        form = SubjectAddForm(instance=subject, school=request.user.school)
=======
        form = SubjectAddForm(instance=subject)
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e

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
<<<<<<< HEAD
    if request.user.school:
        classes = classes.filter(school=request.user.school)
=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
    return render(request, "core/class_list.html", {"classes": classes})


@login_required
@lecturer_required
def class_add_view(request):
<<<<<<< HEAD
    form = SchoolClassForm(request.POST or None, school=request.user.school)
=======
    form = SchoolClassForm(request.POST or None)
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e

    if request.method == "POST":
            print(" POST DATA:", request.POST)

            if form.is_valid():
                print(" VALID FORM")
<<<<<<< HEAD
                school_class = form.save(commit=False)
                school_class.school = request.user.school
                school_class.save()
=======
                form.save()
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
            else:
                print(" FORM ERRORS:", form.errors)

    return render(request, "core/class_form.html", {"form": form})

@login_required
@lecturer_required
def class_update_view(request, pk):
    obj = get_object_or_404(SchoolClass, pk=pk)
<<<<<<< HEAD
    form = SchoolClassForm(request.POST or None, instance=obj, school=request.user.school)
=======
    form = SchoolClassForm(request.POST or None, instance=obj)
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e

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
<<<<<<< HEAD
=======


>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
