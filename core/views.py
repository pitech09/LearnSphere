from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils import timezone
from django.db import transaction
from accounts.decorators import admin_required, lecturer_required
from accounts.models import Parent, User, Student
from course.forms import SubjectAddForm
from course.models import Subject, SubjectAllocation
from result.models import TakenCourse
from result.views import build_quarter_sections, get_current_quarter
from .forms import (
    BulkFeeForm,
    CurrentQuarterForm,
    ExamForm,
    ExamScheduleFormSet,
    MarkEntryByLevelForm,
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


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from accounts.models import User, Student
from .models import SchoolFee, FeePayment, Session, Term
from .forms import SchoolFeeForm, FeePaymentForm


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import TimetableEntry, SchoolClass
from .forms import TimetableEntryForm
from .models import SchoolClass, MarkEntry

from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.decorators import lecturer_required

from django.http import JsonResponse
from course.models import Subject

@login_required
@admin_required
def get_subjects_by_class(request):
    class_id = request.GET.get('class_id')
    if class_id:
        from core.models import SchoolClass
        try:
            school_class = SchoolClass.objects.get(id=class_id)
            level = school_class.level
            # Get all subjects from any class with the same level and same school
            subjects = Subject.objects.filter(
                class_assigned__school=school_class.school,
                class_assigned__level=level
            ).values('id', 'title', 'code').distinct()
            return JsonResponse(list(subjects), safe=False)
        except SchoolClass.DoesNotExist:
            pass
    return JsonResponse([], safe=False)

@login_required
@admin_required
def mark_entry_by_level(request):
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')

    students = []
    mark_entries = []
    form = MarkEntryByLevelForm(request.POST or None, school=school)
    subject = None
    exam = None

    # Handle POST: redirect to GET with query params
    if request.method == 'POST' and form.is_valid():
        level = form.cleaned_data['level']
        subject = form.cleaned_data['subject']
        exam = form.cleaned_data.get('exam')
        url = f"{reverse('mark_entry_by_level')}?level={level}&subject={subject.id}&exam={exam.id if exam else ''}"
        return redirect(url)

    # Handle GET: load students and existing marks
    level = request.GET.get('level')
    subject_id = request.GET.get('subject')
    exam_id = request.GET.get('exam')

    if level and subject_id:
        # Pre‑populate the form for display
        initial = {'level': level, 'subject': subject_id}
        if exam_id:
            initial['exam'] = exam_id
        form = MarkEntryByLevelForm(initial=initial, school=school)

        try:
            subject = Subject.objects.get(id=subject_id, school=school)
            exam = Exam.objects.get(id=exam_id) if exam_id else None
        except Subject.DoesNotExist:
            messages.error(request, "Subject not found.")
            return redirect('mark_entry_by_level')

        # Get all classes under the chosen level
        classes = SchoolClass.objects.filter(school=school, level=level)
        # Get all students in those classes
        students = Student.objects.filter(student_class__in=classes, student__school=school).select_related('student')

        # Retrieve existing marks
        existing = MarkEntry.objects.filter(student__in=students, subject=subject, exam=exam)
        mark_dict = {me.student_id: me for me in existing}

        for student in students:
            mark = mark_dict.get(student.id)
            mark_entries.append({
                'student': student,
                'ca': mark.continuous_assessment if mark else '',
                'exam_mark': mark.exam_mark if mark else '',
                'mark_id': mark.id if mark else None,
            })

    return render(request, 'marks/mark_entry_form.html', {
        'form': form,
        'students': students,
        'mark_entries': mark_entries,
        'subject': subject,
        'exam': exam,
    })

@login_required
@admin_required
def mark_entry_by_level(request):
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated.")
        return redirect('dashboard')

    students = []
    mark_entries = []
    if request.method == 'POST':
        form = MarkEntryByLevelForm(request.POST, school=school)
        if form.is_valid():
            level = form.cleaned_data['level']
            subject = form.cleaned_data['subject']
            exam = form.cleaned_data.get('exam')

            # Clear any previous data to avoid Decimal contamination
            if 'mark_form_data' in request.session:
                del request.session['mark_form_data']

            # Store only JSON‑serializable values
            request.session['mark_form_data'] = {
                'level': str(level),                 # force string
                'subject_id': int(subject.id),       # force int
                'exam_id': int(exam.id) if exam else None,
            }
            request.session.modified = True      # mark as changed

        else:
            messages.error(request, "Invalid form.")
            return render(request, 'marks/mark_entry_form.html', {'form': form})
    else:
        form = MarkEntryByLevelForm(school=school)

        # If there is saved data, pre-populate form
        if 'mark_form_data' in request.session:
            data = request.session['mark_form_data']
            form = MarkEntryByLevelForm(initial={
                'level': data.get('level'),
                'subject': data.get('subject_id'),
                'exam': data.get('exam_id'),
                'continuous_assessment': data.get('ca'),
                'exam_mark': data.get('exam_mark'),
            }, school=school)

    return render(request, 'marks/mark_entry_form.html', {
        'form': form,
        'students': students,
        'mark_entries': mark_entries,
    })

@login_required
@admin_required
def save_marks(request):
    if request.method == 'POST':
        school = getattr(request.user, 'school', None)
        if not school:
            return JsonResponse({'error': 'No school'}, status=400)

        # Get list of student IDs and marks
        student_ids = request.POST.getlist('student_id')
        ca_marks = request.POST.getlist('ca')
        exam_marks = request.POST.getlist('exam_mark')
        mark_ids = request.POST.getlist('mark_id')
        subject_id = request.POST.get('subject_id')
        exam_id = request.POST.get('exam_id')

        try:
            subject = Subject.objects.get(id=subject_id, school=school)
            exam = Exam.objects.get(id=exam_id) if exam_id else None
        except (Subject.DoesNotExist, Exam.DoesNotExist):
            return JsonResponse({'error': 'Invalid subject or exam'}, status=400)

        saved = 0
        for i, student_id in enumerate(student_ids):
            if not student_id:
                continue
            ca = ca_marks[i] if i < len(ca_marks) else 0
            exam_m = exam_marks[i] if i < len(exam_marks) else 0
            mark_id = mark_ids[i] if i < len(mark_ids) else None

            if mark_id:
                # Update existing
                mark = MarkEntry.objects.get(id=mark_id, student_id=student_id, subject=subject)
                mark.continuous_assessment = ca
                mark.exam_mark = exam_m
                mark.save()
            else:
                # Create new
                MarkEntry.objects.create(
                    school=school,
                    student_id=student_id,
                    subject=subject,
                    exam=exam,
                    continuous_assessment=ca,
                    exam_mark=exam_m,
                    status='draft',
                )
            saved += 1

        messages.success(request, f"Saved marks for {saved} students.")
        return redirect('mark_entry_by_level')

    return redirect('mark_entry_by_level')


@login_required
@admin_required
def timetable_list(request):
    school = getattr(request.user, 'school', None)
    entries = TimetableEntry.objects.select_related('school_class', 'subject', 'teacher')
    if school:
        entries = entries.filter(school=school)
    else:
        entries = entries.none()

    # Filters
    class_id = request.GET.get('class')
    day = request.GET.get('day')
    teacher_id = request.GET.get('teacher')

    if class_id:
        entries = entries.filter(school_class_id=class_id)
    if day:
        entries = entries.filter(day=day)
    if teacher_id:
        entries = entries.filter(teacher_id=teacher_id)

    paginator = Paginator(entries.order_by('school_class', 'day', 'start_time'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'classes': SchoolClass.objects.filter(school=school) if school else [],
        'teachers': User.objects.filter(school=school, is_lecturer=True) if school else [],
        'days': TimetableEntry._meta.get_field('day').choices,
        'selected_class': class_id,
        'selected_day': day,
        'selected_teacher': teacher_id,
    }
    return render(request, 'timetable/timetable_list.html', context)

@login_required
@admin_required
def timetable_add(request):
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = TimetableEntryForm(request.POST, school=school)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.school = school
            entry.save()
            messages.success(request, "Timetable entry added.")
            return redirect('timetable_list')
    else:
        form = TimetableEntryForm(school=school)

    return render(request, 'timetable/timetable_form.html', {'form': form, 'title': 'Add Timetable Entry'})

@login_required
@admin_required
def timetable_edit(request, pk):
    school = getattr(request.user, 'school', None)
    entry = get_object_or_404(TimetableEntry, pk=pk, school=school)

    if request.method == 'POST':
        form = TimetableEntryForm(request.POST, instance=entry, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, "Timetable entry updated.")
            return redirect('timetable_list')
    else:
        form = TimetableEntryForm(instance=entry, school=school)

    return render(request, 'timetable/timetable_form.html', {'form': form, 'title': 'Edit Timetable Entry'})

@login_required
@admin_required
def timetable_delete(request, pk):
    school = getattr(request.user, 'school', None)
    entry = get_object_or_404(TimetableEntry, pk=pk, school=school)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, "Timetable entry deleted.")
        return redirect('timetable_list')
    return render(request, 'core/confirm_delete.html', {'object': entry, 'cancel_url': 'timetable_list'})


@login_required
@admin_required
def exam_list(request):
    school = getattr(request.user, 'school', None)
    exams = Exam.objects.select_related('school_class', 'session', 'term')
    if school:
        exams = exams.filter(school=school)
    else:
        exams = exams.none()

    # Filters
    class_id = request.GET.get('class')
    session_id = request.GET.get('session')
    term_id = request.GET.get('term')
    status = request.GET.get('status')

    if class_id:
        exams = exams.filter(school_class_id=class_id)
    if session_id:
        exams = exams.filter(session_id=session_id)
    if term_id:
        exams = exams.filter(term_id=term_id)
    if status:
        exams = exams.filter(status=status)

    paginator = Paginator(exams.order_by('-starts_on'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'classes': SchoolClass.objects.filter(school=school) if school else [],
        'sessions': Session.objects.filter(school=school) if school else [],
        'terms': Term.objects.filter(school=school) if school else [],
        'status_choices': Exam._meta.get_field('status').choices,
        'selected_class': class_id,
        'selected_session': session_id,
        'selected_term': term_id,
        'selected_status': status,
    }
    return render(request, 'exams/exam_list.html', context)

@login_required
@admin_required
def exam_add(request):
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ExamForm(request.POST, school=school)
        formset = ExamScheduleFormSet(request.POST, form_kwargs={'school': school})
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                exam = form.save(commit=False)
                exam.school = school
                exam.save()
                formset.instance = exam
                formset.save()
            messages.success(request, f"Exam '{exam.name}' added successfully.")
            return redirect('exam_list')
    else:
        form = ExamForm(school=school)
        formset = ExamScheduleFormSet(form_kwargs={'school': school})

    return render(request, 'exams/exam_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Add Exam'
    })


@login_required
@admin_required
def exam_edit(request, pk):
    school = getattr(request.user, 'school', None)
    exam = get_object_or_404(Exam, pk=pk, school=school)

    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam, school=school)
        formset = ExamScheduleFormSet(request.POST, instance=exam, form_kwargs={'school': school})
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, f"Exam '{exam.name}' updated.")
            return redirect('exam_list')
    else:
        form = ExamForm(instance=exam, school=school)
        formset = ExamScheduleFormSet(instance=exam, form_kwargs={'school': school})

    return render(request, 'exams/exam_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit Exam'
    })


@login_required
@admin_required
def exam_delete(request, pk):
    school = getattr(request.user, 'school', None)
    exam = get_object_or_404(Exam, pk=pk, school=school)
    if request.method == 'POST':
        name = exam.name
        exam.delete()
        messages.success(request, f"Exam '{name}' deleted.")
        return redirect('exam_list')
    return render(request, 'core/confirm_delete.html', {'object': exam, 'cancel_url': 'exam_list'})

@login_required
@admin_required
def exam_detail(request, pk):
    school = getattr(request.user, 'school', None)
    exam = get_object_or_404(Exam, pk=pk, school=school)
    schedules = exam.schedule_entries.all().select_related('subject', 'invigilator')
    return render(request, 'exams/exam_detail.html', {'exam': exam, 'schedules': schedules})


@login_required
@admin_required
def fee_list(request):
    """List all school fees for the user's school."""
    fees = SchoolFee.objects.select_related('student__student', 'session', 'term')
    school = getattr(request.user, 'school', None)
    if school:
        fees = fees.filter(school=school)
    else:
        fees = fees.none()

    # Filters
    student_id = request.GET.get('student')
    session_id = request.GET.get('session')
    term_id = request.GET.get('term')
    status = request.GET.get('status')

    if student_id:
        fees = fees.filter(student_id=student_id)
    if session_id:
        fees = fees.filter(session_id=session_id)
    if term_id:
        fees = fees.filter(term_id=term_id)
    if status:
        fees = fees.filter(status=status)

    # Pagination
    paginator = Paginator(fees.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'students': Student.objects.filter(student__school=school).select_related('student') if school else [],
        'sessions': Session.objects.filter(school=school) if school else [],
        'terms': Term.objects.filter(school=school) if school else [],
        'status_choices': SchoolFee._meta.get_field('status').choices,
        'selected_student': student_id,
        'selected_session': session_id,
        'selected_term': term_id,
        'selected_status': status,
    }
    return render(request, 'fees/fee_list.html', context)

@login_required
@admin_required
def fee_add(request):
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('fee_list')

    if request.method == 'POST':
        form = SchoolFeeForm(request.POST, school=school)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.school = school
            fee.save()
            messages.success(request, f"Fee for {fee.student} added successfully.")
            return redirect('fee_list')
    else:
        form = SchoolFeeForm(school=school)

    return render(request, 'fees/fee_form.html', {'form': form, 'title': 'Add Fee'})

@login_required
@admin_required
def fee_edit(request, pk):
    school = getattr(request.user, 'school', None)
    fee = get_object_or_404(SchoolFee, pk=pk, school=school)

    if request.method == 'POST':
        form = SchoolFeeForm(request.POST, instance=fee, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, f"Fee for {fee.student} updated.")
            return redirect('fee_list')
    else:
        form = SchoolFeeForm(instance=fee, school=school)

    return render(request, 'fees/fee_form.html', {'form': form, 'title': 'Edit Fee'})

@login_required
@admin_required
def fee_delete(request, pk):
    school = getattr(request.user, 'school', None)
    fee = get_object_or_404(SchoolFee, pk=pk, school=school)
    if request.method == 'POST':
        student_name = str(fee.student)
        fee.delete()
        messages.success(request, f"Fee for {student_name} deleted.")
        return redirect('fee_list')
    return render(request, 'core/confirm_delete.html', {'object': fee, 'cancel_url': 'fee_list'})

@login_required
@admin_required
def fee_detail(request, pk):
    school = getattr(request.user, 'school', None)
    fee = get_object_or_404(SchoolFee, pk=pk, school=school)
    payments = fee.payments.all().order_by('-paid_on')
    return render(request, 'fees/fee_detail.html', {'fee': fee, 'payments': payments})

@login_required
@admin_required
def payment_add(request, fee_pk):
    school = getattr(request.user, 'school', None)
    fee = get_object_or_404(SchoolFee, pk=fee_pk, school=school)

    if request.method == 'POST':
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.fee = fee
            payment.received_by = request.user
            payment.save()
            messages.success(request, f"Payment of {payment.amount} recorded.")
            return redirect('fee_detail', pk=fee.pk)
    else:
        form = FeePaymentForm(initial={'paid_on': timezone.localdate()})

    return render(request, 'fees/payment_form.html', {'form': form, 'fee': fee})


@login_required
@admin_required
def bulk_fee_add(request):
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = BulkFeeForm(request.POST, school=school)
        if form.is_valid():
            school_class = form.cleaned_data['school_class']
            session = form.cleaned_data['session']
            term = form.cleaned_data['term']
            description = form.cleaned_data['description']
            amount_due = form.cleaned_data['amount_due']
            discount = form.cleaned_data.get('discount', 0)
            due_date = form.cleaned_data.get('due_date')

            # Get all students in the class
            students = Student.objects.filter(student_class=school_class, student__school=school)
            created_count = 0
            skipped = 0
            for student in students:
                # Avoid duplicate fee for same student, session, term, description (optional)
                if SchoolFee.objects.filter(student=student, session=session, term=term, description=description).exists():
                    skipped += 1
                    continue
                SchoolFee.objects.create(
                    school=school,
                    student=student,
                    session=session,
                    term=term,
                    description=description,
                    amount_due=amount_due,
                    discount=discount,
                    due_date=due_date,
                    status='pending'
                )
                created_count += 1

            messages.success(request, f"Created {created_count} fee records. Skipped {skipped} duplicates.")
            return redirect('fee_list')
    else:
        form = BulkFeeForm(school=school)

    return render(request, 'fees/bulk_fee_form.html', {'form': form, 'title': 'Bulk Add Fees'})
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
    current_assessments = (
        courses.filter(quarter=current_quarter)
        if current_quarter
        else courses.none()
    )

    return render(request, "core/student_dashboard.html", {
        "school": request.user.school,
        "student": student,
        "subjects": subjects[:8],
        "subject_count": subjects.count(),
        "registered_count": courses.count(),
        "current_quarter": current_quarter,
        "current_section": current_section,
        "current_assessments": current_assessments,
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
def session_list_view(request):
    sessions = Session.objects.all().order_by("-is_current", "-session")
    if request.user.school:
        sessions = sessions.filter(school=request.user.school)
    return render(request, "core/session_list.html", {
        "sessions": sessions
    })


@login_required
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
def subject_list_view(request):
    subjects = Subject.objects.select_related("school", "class_assigned", "teacher")
    if request.user.school:
        subjects = subjects.filter(school=request.user.school)
    return render(request, "core/subject_list.html", {"subjects": subjects})


@login_required
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
def class_list_view(request):
    classes = SchoolClass.objects.select_related("class_teacher", "school")
    if request.user.school:
        classes = classes.filter(school=request.user.school)
    return render(request, "core/class_list.html", {"classes": classes})


@login_required
@admin_required
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
@admin_required
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
@admin_required
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


# =========================================================
# AUTO TIMETABLE GENERATION
# =========================================================
from datetime import time, timedelta
from .forms import AutoTimetableForm
from course.models import Subject


@login_required
@admin_required
def auto_generate_timetable(request):
    """
    Auto-generate timetable for all classes, avoiding clashes.
    Algorithm:
    1. Get all classes, subjects with teachers, and time slots
    2. For each class, assign subjects to available time slots
    3. Ensure no teacher teaches two classes at the same time
    4. Ensure no class has two subjects at the same time
    """
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AutoTimetableForm(request.POST)
        if form.is_valid():
            periods_per_day = int(form.cleaned_data['periods_per_day'])
            period_duration = int(form.cleaned_data['period_duration'])
            start_hour = int(form.cleaned_data['start_time'].hour)
            start_minute = int(form.cleaned_data['start_time'].minute)
            days = form.cleaned_data['days']
            clear_existing = form.cleaned_data['clear_existing']
            school_hours = int(form.cleaned_data['school_hours'])
            max_subject_per_day = int(form.cleaned_data['max_subject_per_day'])
            
            # Get all active classes for the school
            classes = SchoolClass.objects.filter(school=school, is_active=True)
            
            # Get all subjects with teachers for the school
            subjects = Subject.objects.filter(
                school=school,
                teacher__isnull=False
            ).select_related('teacher', 'class_assigned')
            
            if clear_existing:
                TimetableEntry.objects.filter(school=school).delete()
            
            # Calculate school end time based on school_hours
            school_end_minutes = (start_hour * 60 + start_minute) + (school_hours * 60)
            school_end_hour = school_end_minutes // 60
            school_end_min = school_end_minutes % 60
            if school_end_hour >= 24:
                school_end_hour = 23
                school_end_min = 59
            school_end_time = time(school_end_hour, school_end_min)
            
            # Generate time slots (only within school hours)
            time_slots = []
            current_time = time(start_hour, start_minute)
            for _ in range(periods_per_day):
                end_minutes = current_time.hour * 60 + current_time.minute + period_duration
                end_hour = end_minutes // 60
                end_min = end_minutes % 60
                if end_hour >= 24:
                    end_hour = 23
                    end_min = 59
                end_time_obj = time(end_hour, end_min)
                
                # Check if this period ends within school hours
                if end_time_obj > school_end_time:
                    break
                    
                time_slots.append((current_time, end_time_obj))
                # Next period starts 5 minutes after current ends (break time)
                next_minutes = end_minutes + 5
                next_hour = next_minutes // 60
                next_min = next_minutes % 60
                if next_hour >= 24:
                    break
                current_time = time(next_hour, next_min)
            
            # Track teacher and class assignments to avoid clashes
            # Key: (day, time_slot_index) -> set of teacher_ids
            teacher_schedule = {day: {i: set() for i in range(len(time_slots))} for day in days}
            # Key: (day, time_slot_index) -> set of class_ids  
            class_schedule = {day: {i: set() for i in range(len(time_slots))} for day in days}
            # Track subject count per day per class: {(class_id, day, subject_id): count}
            subject_day_count = {}
            
            created_count = 0
            
            # For each class, assign its subjects
            for school_class in classes:
                # Get subjects for this class
                class_subjects = subjects.filter(class_assigned=school_class)
                
                if not class_subjects.exists():
                    continue
                
                # Distribute subjects across the week
                subject_list = list(class_subjects)
                periods_per_subject = max(1, len(time_slots) * len(days) // max(len(subject_list), 1))
                
                for subject in subject_list:
                    periods_assigned = 0
                    teacher = subject.teacher
                    
                    # Try to assign this subject to available slots
                    for day in days:
                        if periods_assigned >= periods_per_subject:
                            break
                            
                        for slot_idx, (start_t, end_t) in enumerate(time_slots):
                            if periods_assigned >= periods_per_subject:
                                break
                            
                            # Check if teacher is available
                            if teacher.id in teacher_schedule[day][slot_idx]:
                                continue
                            
                            # Check if class is available
                            if school_class.id in class_schedule[day][slot_idx]:
                                continue
                            
                            # Check max subject per day constraint
                            count_key = (school_class.id, day, subject.id)
                            current_count = subject_day_count.get(count_key, 0)
                            if current_count >= max_subject_per_day:
                                continue
                            
                            # Check if this exact entry already exists
                            existing = TimetableEntry.objects.filter(
                                school=school,
                                school_class=school_class,
                                day=day,
                                start_time=start_t
                            ).exists()
                            
                            if existing:
                                continue
                            
                            # Create the timetable entry
                            TimetableEntry.objects.create(
                                school=school,
                                school_class=school_class,
                                subject=subject,
                                teacher=teacher,
                                day=day,
                                start_time=start_t,
                                end_time=end_t,
                                is_active=True
                            )
                            
                            # Mark teacher and class as busy
                            teacher_schedule[day][slot_idx].add(teacher.id)
                            class_schedule[day][slot_idx].add(school_class.id)
                            
                            # Update subject day count
                            subject_day_count[count_key] = current_count + 1
                            
                            created_count += 1
                            periods_assigned += 1
            
            messages.success(request, f"Successfully created {created_count} timetable entries.")
            return redirect('timetable_list')
    else:
        form = AutoTimetableForm()
    
    # Get stats for display
    classes = SchoolClass.objects.filter(school=school, is_active=True)
    subjects = Subject.objects.filter(school=school, teacher__isnull=False)
    teachers = User.objects.filter(school=school, is_lecturer=True)
    existing_entries = TimetableEntry.objects.filter(school=school)
    
    return render(request, 'timetable/auto_generate.html', {
        'form': form,
        'classes': classes,
        'subjects': subjects,
        'teachers': teachers,
        'existing_entries_count': existing_entries.count(),
    })


@login_required
@admin_required
def class_timetable_print(request, class_id):
    """
    Display and print timetable for a specific class in a clean grid format.
    """
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')
    
    school_class = get_object_or_404(SchoolClass, pk=class_id, school=school)
    
    # Get all timetable entries for this class
    entries = TimetableEntry.objects.filter(
        school=school,
        school_class=school_class,
        is_active=True
    ).select_related('subject', 'teacher').order_by('day', 'start_time')
    
    # Get unique days and time slots
    days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    days = []
    time_slots = []
    
    for entry in entries:
        if entry.day not in days:
            days.append(entry.day)
        time_key = (entry.start_time, entry.end_time)
        if time_key not in time_slots:
            time_slots.append(time_key)
    
    # Sort days according to standard order
    days = sorted(days, key=lambda x: days_order.index(x) if x in days_order else 999)
    # Sort time slots by start time
    time_slots = sorted(time_slots, key=lambda x: x[0])
    
    # Build the timetable grid
    timetable_grid = {}
    for day in days:
        timetable_grid[day] = {}
        for time_slot in time_slots:
            timetable_grid[day][time_slot] = None
    
    # Fill in the grid with entries
    for entry in entries:
        time_key = (entry.start_time, entry.end_time)
        if entry.day in timetable_grid and time_key in timetable_grid[entry.day]:
            timetable_grid[entry.day][time_key] = entry
    
    return render(request, 'timetable/class_timetable_print.html', {
        'school_class': school_class,
        'days': days,
        'time_slots': time_slots,
        'timetable_grid': timetable_grid,
        'school': school,
    })
