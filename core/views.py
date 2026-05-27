from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils import timezone

from accounts.decorators import admin_required, lecturer_required
from accounts.models import Parent, User, Student
from course.forms import SubjectAddForm
from course.models import Subject, SubjectAllocation
from result.models import TakenCourse
from result.views import build_quarter_sections, get_current_quarter
from .forms import (
    CurrentQuarterForm,
    SchoolPlatformForm,
    SessionForm,
    NewsAndEventsForm,
    SubjectForm,
)
from .models import (
    ActivityLog,
    AttendanceRecord,
    Exam,
    FeePayment,
    NewsAndEvents,
    School,
    SchoolClass,
    SchoolFee,
    SCHOOL_STATUS_ACTIVE,
    SCHOOL_STATUS_SUSPENDED,
    SCHOOL_STATUS_TRIAL,
    Session,
    Term,
    TimetableEntry,
)



# =========================================================
# NEWS & EVENTS
# =========================================================
@login_required
def home_view(request):
    items = NewsAndEvents.objects.select_related("school").order_by("-updated_at")
    school = getattr(request.user, "school", None)
    if school:
        items = items.filter(school=school)
    return render(request, "core/index.html", {
        "title": "News & Events",
        "items": items,
    })


# =========================================================
# DASHBOARD
# =========================================================
@login_required
def dashboard_view(request):
    if request.user.is_student:
        return redirect("student_dashboard")
    if request.user.is_lecturer and not request.user.is_superuser:
        return redirect("teacher_dashboard")
    if request.user.is_superuser and getattr(request.user, "school_id", None):
        return redirect("principal_dashboard")
    if request.user.is_superuser and not getattr(request.user, "school_id", None):
        return redirect("platform_owner_dashboard")
    return redirect("home")


@login_required
@admin_required
def principal_dashboard(request):
    school = getattr(request.user, "school", None)
    if request.user.is_superuser and not school:
        return redirect("platform_owner_dashboard")

    users = User.objects.all()
    students = Student.objects.select_related("student", "student_class")
    classes = SchoolClass.objects.select_related("school", "class_teacher")
    fees = SchoolFee.objects.select_related("school", "student__student", "session", "term")
    payments = FeePayment.objects.select_related("fee__school", "received_by")
    exams = Exam.objects.select_related("school", "school_class", "session", "term")
    timetable = TimetableEntry.objects.select_related("school", "school_class", "subject", "teacher")
    attendance = AttendanceRecord.objects.select_related("school", "student__student", "school_class", "subject")
    marks = TakenCourse.objects.select_related("school", "student__student", "course")
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]

    if school:
        users = users.filter(school=school)
        students = students.filter(student__school=school)
        classes = classes.filter(school=school)
        fees = fees.filter(school=school)
        payments = payments.filter(fee__school=school)
        exams = exams.filter(school=school)
        timetable = timetable.filter(school=school)
        attendance = attendance.filter(school=school)
        marks = marks.filter(school=school)

    males_count = students.filter(student__gender="M").count()
    females_count = students.filter(student__gender="F").count()
    attendance_total = attendance.count()
    attendance_present = attendance.filter(status="present").count()
    attendance_rate = round((attendance_present / attendance_total) * 100, 1) if attendance_total else 0
    collected_fees = payments.aggregate(total=Sum("amount"))["total"] or 0
    fee_totals = fees.aggregate(
        amount_due=Sum("amount_due"),
        discount=Sum("discount"),
    )
    paid_total = payments.aggregate(total=Sum("amount"))["total"] or 0
    outstanding_fees = (
        (fee_totals["amount_due"] or 0)
        - (fee_totals["discount"] or 0)
        - paid_total
    )
    marked_courses = marks.exclude(total__isnull=True)
    average_mark = 0
    if marked_courses.exists():
        average_mark = sum(course.total for course in marked_courses) / marked_courses.count()

    return render(request, "core/dashboard.html", {
        "school": school,
        "student_count": users.filter(is_student=True).count(),
        "lecturer_count": users.filter(is_lecturer=True).count(),
        "parent_count": Parent.objects.filter(user__school=school).count() if school else Parent.objects.count(),
        "class_count": classes.filter(is_active=True).count(),
        "attendance_rate": attendance_rate,
        "exam_count": exams.count(),
        "timetable_count": timetable.count(),
        "collected_fees": collected_fees,
        "outstanding_fees": outstanding_fees,
        "average_mark": average_mark,
        "upcoming_exams": exams.filter(starts_on__gte=timezone.localdate()).order_by("starts_on")[:5],
        "males_count": males_count,
        "females_count": females_count,
        "logs": logs,
    })


@login_required
@lecturer_required
def teacher_dashboard(request):
    school = getattr(request.user, "school", None)
    if request.user.is_superuser:
        return redirect("dashboard")
    if not school:
        return redirect("home")

    subjects = Subject.objects.select_related("class_assigned").filter(
        Q(teacher=request.user) | Q(allocated_subjects__teacher=request.user),
        school=school,
    ).distinct()
    class_ids = subjects.exclude(class_assigned__isnull=True).values_list("class_assigned_id", flat=True).distinct()
    students = Student.objects.select_related("student", "student_class").filter(
        student__school=school,
        student_class_id__in=class_ids,
    )
    current_quarter = get_current_quarter(school)
    marks = TakenCourse.objects.select_related("student__student", "course").filter(
        school=school,
        course__in=subjects,
        quarter=current_quarter,
    )
    upcoming_exams = Exam.objects.select_related("school_class").filter(
        school=school,
        school_class_id__in=class_ids,
        starts_on__gte=timezone.localdate(),
    ).order_by("starts_on")[:5]

    average_mark = 0
    if marks.exists():
        average_mark = sum(mark.total for mark in marks) / marks.count()

    return render(request, "core/teacher_dashboard.html", {
        "school": school,
        "subjects": subjects[:8],
        "subject_count": subjects.count(),
        "student_count": students.count(),
        "marked_count": marks.count(),
        "average_mark": average_mark,
        "current_quarter": current_quarter,
        "upcoming_exams": upcoming_exams,
    })


@login_required
def student_dashboard(request):
    if not request.user.is_student:
        return redirect("dashboard")

    student = get_object_or_404(
        Student.objects.select_related("student", "student_class"),
        student=request.user,
        student__school=request.user.school,
    )
    subjects = Subject.objects.select_related("class_assigned", "teacher").filter(
        school=request.user.school,
        class_assigned=student.student_class,
    )
    courses = TakenCourse.objects.select_related("course").filter(
        school=request.user.school,
        student=student,
    ).order_by("quarter", "course__title")
    quarter_sections = build_quarter_sections(courses)
    current_quarter = get_current_quarter(request.user.school)
    current_section = next(
        (section for section in quarter_sections if section["code"] == current_quarter),
        quarter_sections[0] if quarter_sections else None,
    )

    return render(request, "core/student_dashboard.html", {
        "school": request.user.school,
        "student": student,
        "subjects": subjects[:8],
        "subject_count": subjects.count(),
        "registered_count": courses.count(),
        "current_quarter": current_quarter,
        "current_section": current_section,
    })


def platform_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return view_func(request, *args, **kwargs)
        messages.error(request, "Only the platform administrator can access that page.")
        return redirect("dashboard")
    return wrapper


@login_required
@platform_admin_required
def platform_owner_dashboard(request):
    all_schools = School.objects.all()

    total_schools = all_schools.count()
    active_count = all_schools.filter(status=SCHOOL_STATUS_ACTIVE, is_active=True).count()
    trial_count = all_schools.filter(status=SCHOOL_STATUS_TRIAL).count()
    suspended_count = all_schools.filter(status=SCHOOL_STATUS_SUSPENDED).count()
    overdue_count = all_schools.filter(next_payment_due_on__lt=timezone.localdate()).count()
    monthly_revenue = all_schools.filter(status=SCHOOL_STATUS_ACTIVE).aggregate(
        total=Sum("subscription_amount")
    )["total"] or 0
    total_users = User.objects.count()
    total_teachers = User.objects.filter(is_lecturer=True).count()
    recent_schools = all_schools.order_by("-created_at")[:10]

    return render(request, "core/platform_owner_dashboard.html", {
        "total_schools": total_schools,
        "active_count": active_count,
        "trial_count": trial_count,
        "suspended_count": suspended_count,
        "overdue_count": overdue_count,
        "monthly_revenue": monthly_revenue,
        "total_users": total_users,
        "total_teachers": total_teachers,
        "recent_schools": recent_schools,
    })


@login_required
@platform_admin_required
def platform_schools_dashboard(request):
    all_schools = School.objects.all()
    schools = all_schools.order_by("name")
    status_filter = request.GET.get("status")
    if status_filter:
        schools = schools.filter(status=status_filter)

    total_schools = all_schools.count()
    active_count = all_schools.filter(status=SCHOOL_STATUS_ACTIVE, is_active=True).count()
    suspended_count = all_schools.filter(status=SCHOOL_STATUS_SUSPENDED).count()
    overdue_count = all_schools.filter(next_payment_due_on__lt=timezone.localdate()).count()
    monthly_revenue = all_schools.filter(status=SCHOOL_STATUS_ACTIVE).aggregate(
        total=Sum("subscription_amount")
    )["total"] or 0

    return render(request, "core/platform_schools_dashboard.html", {
        "schools": schools,
        "total_schools": total_schools,
        "active_count": active_count,
        "suspended_count": suspended_count,
        "overdue_count": overdue_count,
        "monthly_revenue": monthly_revenue,
        "status_filter": status_filter,
    })


@login_required
@platform_admin_required
def platform_school_update(request, pk):
    school = get_object_or_404(School, pk=pk)
    form = SchoolPlatformForm(request.POST or None, instance=school)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{school.name} billing and status updated.")
        return redirect("platform_schools_dashboard")
    student_count = User.objects.filter(school=school, is_student=True).count()
    return render(request, "core/platform_school_form.html", {
        "form": form,
        "school": school,
        "student_count": student_count,
    })


@login_required
@platform_admin_required
def platform_school_suspend(request, pk):
    school = get_object_or_404(School, pk=pk)
    if request.method == "POST":
        school.status = SCHOOL_STATUS_SUSPENDED
        school.is_active = False
        school.suspended_reason = request.POST.get("suspended_reason") or "Service suspended for non-payment."
        school.save(update_fields=["status", "is_active", "suspended_reason", "updated_at"])
        messages.success(request, f"{school.name} has been suspended.")
    return redirect("platform_schools_dashboard")


@login_required
@platform_admin_required
def platform_suspend_overdue_schools(request):
    if request.method == "POST":
        overdue_schools = School.objects.filter(
            next_payment_due_on__lt=timezone.localdate(),
        ).exclude(status=SCHOOL_STATUS_SUSPENDED)
        count = overdue_schools.update(
            status=SCHOOL_STATUS_SUSPENDED,
            is_active=False,
            suspended_reason="Service suspended for overdue subscription payment.",
            updated_at=timezone.now(),
        )
        messages.success(request, f"{count} overdue school(s) suspended.")
    return redirect("platform_schools_dashboard")


@login_required
@platform_admin_required
def platform_school_reactivate(request, pk):
    school = get_object_or_404(School, pk=pk)
    if request.method == "POST":
        school.status = SCHOOL_STATUS_ACTIVE
        school.is_active = True
        school.suspended_reason = ""
        school.last_payment_on = timezone.localdate()
        school.save(update_fields=["status", "is_active", "suspended_reason", "last_payment_on", "updated_at"])
        messages.success(request, f"{school.name} has been reactivated.")
    return redirect("platform_schools_dashboard")


@login_required
@admin_required
def current_quarter_update(request):
    school = getattr(request.user, "school", None)
    if not school:
        messages.error(request, "Select a school account before setting a quarter.")
        return redirect("platform_schools_dashboard")

    form = CurrentQuarterForm(request.POST or None, instance=school)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Current quarter updated.")
        return redirect("dashboard")

    return render(request, "core/current_quarter_form.html", {"form": form, "school": school})


# =========================================================
# NEWS POSTING
# =========================================================
@login_required
def post_add(request):
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.school = getattr(request.user, "school", None)
            post.save()
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
    posts = NewsAndEvents.objects.all()
    if request.user.school:
        posts = posts.filter(school=request.user.school)
    post = get_object_or_404(posts, pk=pk)

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
    posts = NewsAndEvents.objects.all()
    if request.user.school:
        posts = posts.filter(school=request.user.school)
    post = get_object_or_404(posts, pk=pk)
    title = post.title
    if request.method != "POST":
        return render(request, "core/confirm_delete.html", {"object": post, "cancel_url": "home"})
    post.delete()

    messages.success(request, f"{title} deleted.")
    return redirect("home")


# =========================================================
# SESSION MANAGEMENT (NO SEMESTER ANYMORE)
# =========================================================
@login_required
def session_list_view(request):
    sessions = Session.objects.all().order_by("-is_current", "-session")
    if request.user.school:
        sessions = sessions.filter(school=request.user.school)
    return render(request, "core/session_list.html", {
        "sessions": sessions
    })


@login_required
def session_add_view(request):
    is_platform_owner = request.user.is_superuser and not getattr(request.user, 'school', None)
    selected_school = None

    # Platform owner: show school selection on GET
    if is_platform_owner and request.method == 'GET':
        schools = School.objects.all()
        return render(request, "core/session_update.html", {
            'form': SessionForm(),
            'schools': schools,
        })

    # Platform owner: process POST with school selection
    if is_platform_owner and request.method == 'POST':
        school_id = request.POST.get('school')
        if not school_id:
            messages.error(request, "Please select a school.")
            return render(request, "core/session_update.html", {
                'form': SessionForm(),
                'schools': School.objects.all(),
            })
        selected_school = get_object_or_404(School, pk=school_id)
    else:
        # Normal user (already belongs to a school)
        if not request.user.school:
            messages.error(request, "A school account is required to manage sessions.")
            return redirect("dashboard")
        selected_school = request.user.school

    # Handle POST for all users (including platform owner after school selection)
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            # If this session is set as current, unset any other current session for the same school
            if form.cleaned_data.get("is_current"):
                Session.objects.filter(school=selected_school, is_current=True).update(is_current=False)

            session = form.save(commit=False)
            session.school = selected_school
            try:
                session.save()
                messages.success(request, "Session added.")
                return redirect("session_list")
            except IntegrityError:
                messages.error(request, f"A session named '{session.session}' already exists for this school. Please use a different name.")
                # Re-render form with errors; platform owners need the school dropdown again
                context = {'form': form}
                if is_platform_owner:
                    context['schools'] = School.objects.all()
                    # Optionally, pre-select the previously chosen school in the dropdown
                    # by adding a 'selected' attribute in the template logic
                return render(request, "core/session_update.html", context)
        # else: form invalid, will re-render with errors
    else:
        form = SessionForm()

    # Prepare context for GET (or re-render after error)
    context = {'form': form}
    if is_platform_owner:
        context['schools'] = School.objects.all()
    return render(request, "core/session_update.html", context)


@login_required
@lecturer_required
def session_update_view(request, pk):
    sessions = Session.objects.all()
    if request.user.school:
        sessions = sessions.filter(school=request.user.school)
    session = get_object_or_404(sessions, pk=pk)

    if request.method == "POST":
        form = SessionForm(request.POST, instance=session)

        if form.is_valid():
            if form.cleaned_data.get("is_current"):
                Session.objects.filter(school=session.school, is_current=True).exclude(pk=session.pk).update(is_current=False)

            form.save()
            messages.success(request, "Session updated.")
            return redirect("session_list")

    else:
        form = SessionForm(instance=session)

    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_delete_view(request, pk):
    sessions = Session.objects.all()
    if request.user.school:
        sessions = sessions.filter(school=request.user.school)
    session = get_object_or_404(sessions, pk=pk)

    if request.method != "POST":
        return render(request, "core/confirm_delete.html", {"object": session, "cancel_url": "session_list"})

    if session.is_current:
        messages.error(request, "You cannot delete the current session.")
    else:
        session.delete()
        messages.success(request, "Session deleted.")

    return redirect("session_list")

@login_required
@lecturer_required
def subject_list_view(request):
    subjects = Subject.objects.select_related("school", "class_assigned", "teacher")
    if request.user.school:
        subjects = subjects.filter(school=request.user.school)
    return render(request, "core/subject_list.html", {"subjects": subjects})


@login_required
@lecturer_required
def subject_add_view(request):
    if request.method == "POST":
        form = SubjectAddForm(request.POST, school=request.user.school)

        if form.is_valid():
            subject = form.save(commit=False)
            subject.school = request.user.school
            subject.save()
            messages.success(request, "Subject added.")
            return redirect("subject_list_view")
    else:
        form = SubjectAddForm(school=request.user.school)

    return render(request, "core/subject_form.html", {"form": form})

@login_required
@lecturer_required
def subject_update_view(request, pk):
    subjects = Subject.objects.all()
    if request.user.school:
        subjects = subjects.filter(school=request.user.school)
    subject = get_object_or_404(subjects, pk=pk)

    if request.method == "POST":
        form = SubjectAddForm(request.POST, instance=subject, school=request.user.school)

        if form.is_valid():
            form.save()
            messages.success(request, "Subject updated.")
            return redirect("subject_list_view")

    else:
        form = SubjectAddForm(instance=subject, school=request.user.school)

    return render(request, "core/subject_form.html", {"form": form})

@login_required
@lecturer_required
def subject_delete_view(request, pk):
    subjects = Subject.objects.all()
    if request.user.school:
        subjects = subjects.filter(school=request.user.school)
    subject = get_object_or_404(subjects, pk=pk)

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
    classes = SchoolClass.objects.select_related("class_teacher", "school")
    if request.user.school:
        classes = classes.filter(school=request.user.school)
    return render(request, "core/class_list.html", {"classes": classes})


@login_required
@lecturer_required
def class_add_view(request):
    form = SchoolClassForm(request.POST or None, school=request.user.school)

    if request.method == "POST":
            if form.is_valid():
                school_class = form.save(commit=False)
                school_class.school = request.user.school
                school_class.save()
                messages.success(request, "Class saved.")
                return redirect("class_list")

    return render(request, "core/class_form.html", {"form": form})

@login_required
@lecturer_required
def class_update_view(request, pk):
    classes = SchoolClass.objects.all()
    if request.user.school:
        classes = classes.filter(school=request.user.school)
    obj = get_object_or_404(classes, pk=pk)
    form = SchoolClassForm(request.POST or None, instance=obj, school=request.user.school)

    if form.is_valid():
        form.save()
        messages.success(request, "Class updated successfully")
        return redirect("class_list")

    return render(request, "core/class_form.html", {"form": form})


@login_required
@lecturer_required
def class_delete_view(request, pk):
    classes = SchoolClass.objects.all()
    if request.user.school:
        classes = classes.filter(school=request.user.school)
    obj = get_object_or_404(classes, pk=pk)

    if request.method == "POST":
        obj.delete()
        messages.success(request, "Class deleted")
        return redirect("class_list")

    return render(request, "core/confirm_delete.html", {"object": obj})
