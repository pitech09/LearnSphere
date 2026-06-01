from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import admin_required
from accounts.models import Parent, Student
from core.models import (
    NewsAndEvents,
    SchoolFee,
    Session,
    Term,
    TARGET_ALL,
    TARGET_PARENTS,
)
from course.models import Subject
from result.models import TakenCourse


def parent_required(view_func):
    """Decorator to ensure the user is a parent."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_parent:
            messages.error(request, "Access denied. Parent account required.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@parent_required
def parent_dashboard(request):
    """Parent dashboard showing overview of children, announcements, and fees."""
    school = request.user.school
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect("dashboard")

    # Get all children linked to this parent
    parent_records = Parent.objects.filter(user=request.user).select_related(
        'student__student', 'student__student_class'
    )
    children = [p.student for p in parent_records if p.student]

    # Get parent-specific and general announcements
    announcements = NewsAndEvents.objects.filter(
        Q(school=school),
        Q(target_audience=TARGET_ALL) | Q(target_audience=TARGET_PARENTS)
    ).order_by("-updated_at")[:5]

    # Get fee information for all children
    child_fees = []
    for child in children:
        fees = SchoolFee.objects.filter(
            student=child, school=school
        ).select_related('session', 'term').order_by("-created_at")[:5]
        child_fees.append({
            "student": child,
            "fees": fees,
        })

    # Get current session/term
    current_session = Session.objects.filter(is_current=True, school=school).first()
    current_term = Term.objects.filter(
        is_current=True, session=current_session, school=school
    ).first()

    context = {
        "title": "Parent Portal",
        "children": children,
        "announcements": announcements,
        "child_fees": child_fees,
        "current_session": current_session,
        "current_term": current_term,
        "school": school,
    }
    return render(request, "parent_portal/dashboard.html", context)


@login_required
@parent_required
def parent_child_detail(request, student_id):
    """View details of a specific child."""
    school = request.user.school
    if not school:
        messages.error(request, "No school associated.")
        return redirect("parent_dashboard")

    # Verify the parent owns this student
    parent_record = Parent.objects.filter(
        user=request.user, student_id=student_id
    ).first()
    if not parent_record or not parent_record.student:
        messages.error(request, "You are not authorized to view this student's details.")
        return redirect("parent_dashboard")

    student = parent_record.student

    # Get subjects for the student's class
    subjects = Subject.objects.filter(
        class_assigned=student.student_class, school=school
    )

    # Get current session/term
    current_session = Session.objects.filter(is_current=True, school=school).first()
    current_term = Term.objects.filter(
        is_current=True, session=current_session, school=school
    ).first()

    context = {
        "title": f"{student.student.get_full_name()} - Details",
        "student": student,
        "subjects": subjects,
        "current_session": current_session,
        "current_term": current_term,
        "school": school,
    }
    return render(request, "parent_portal/child_detail.html", context)


@login_required
@parent_required
def parent_grade_reports(request, student_id):
    """View grade reports for a specific child."""
    school = request.user.school
    if not school:
        messages.error(request, "No school associated.")
        return redirect("parent_dashboard")

    # Verify the parent owns this student
    parent_record = Parent.objects.filter(
        user=request.user, student_id=student_id
    ).first()
    if not parent_record or not parent_record.student:
        messages.error(request, "You are not authorized to view this student's grades.")
        return redirect("parent_dashboard")

    student = parent_record.student

    # Get courses/taken courses for this student
    taken_courses = TakenCourse.objects.filter(
        student=student, school=school
    ).select_related('course').order_by('quarter', 'course__title')

    # Group by quarter
    quarters = {}
    for course in taken_courses:
        q = course.quarter
        if q not in quarters:
            quarters[q] = []
        quarters[q].append(course)

    # Calculate overall stats per quarter
    quarter_stats = {}
    for q, courses in quarters.items():
        total_subjects = len(courses)
        total_score = sum(c.total for c in courses)
        average = round(total_score / total_subjects, 2) if total_subjects > 0 else 0
        passed = sum(1 for c in courses if c.comment == "PASS")
        quarter_stats[q] = {
            "total_subjects": total_subjects,
            "total_score": total_score,
            "average": average,
            "passed": passed,
            "failed": total_subjects - passed,
        }

    current_session = Session.objects.filter(is_current=True, school=school).first()

    context = {
        "title": f"{student.student.get_full_name()} - Grade Reports",
        "student": student,
        "quarters": quarters,
        "quarter_stats": quarter_stats,
        "current_session": current_session,
        "school": school,
    }
    return render(request, "parent_portal/grade_reports.html", context)


@login_required
@parent_required
def parent_announcements(request):
    """View all parent-specific and general announcements."""
    school = request.user.school
    if not school:
        messages.error(request, "No school associated.")
        return redirect("parent_dashboard")

    announcements = NewsAndEvents.objects.filter(
        Q(school=school),
        Q(target_audience=TARGET_ALL) | Q(target_audience=TARGET_PARENTS)
    ).order_by("-updated_at")

    context = {
        "title": "School Announcements",
        "announcements": announcements,
        "school": school,
    }
    return render(request, "parent_portal/announcements.html", context)


@login_required
@parent_required
def parent_fees(request, student_id=None):
    """View fee information for children."""
    school = request.user.school
    if not school:
        messages.error(request, "No school associated.")
        return redirect("parent_dashboard")

    parent_records = Parent.objects.filter(user=request.user).select_related(
        'student__student', 'student__student_class'
    )
    children = [p.student for p in parent_records if p.student]

    selected_student = None
    fees = []

    if student_id:
        # Verify parent owns this student
        if Parent.objects.filter(user=request.user, student_id=student_id).exists():
            selected_student = next((c for c in children if c.id == int(student_id)), None)
            if selected_student:
                fees = SchoolFee.objects.filter(
                    student=selected_student, school=school
                ).select_related('session', 'term').order_by("-created_at")
        else:
            messages.error(request, "You are not authorized to view this student's fees.")
            return redirect("parent_fees")

    context = {
        "title": "Fee Information",
        "children": children,
        "selected_student": selected_student,
        "fees": fees,
        "school": school,
    }
    return render(request, "parent_portal/fees.html", context)