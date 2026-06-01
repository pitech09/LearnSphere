import os
from decimal import Decimal, ROUND_HALF_UP

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db.models import Q

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.units import inch
from reportlab.lib import colors

from core.models import Session, Term
from course.models import Subject as Course
from accounts.models import Student
from accounts.decorators import lecturer_required, student_required
from .models import FAIL, GRADE_BOUNDARIES, PASS, QUARTER_CHOICES, TakenCourse, Result


CM = 2.54
PASS_MARK = 45


def get_current_session(school=None):
    sessions = Session.objects.filter(is_current=True)
    if school:
        sessions = sessions.filter(school=school)
    return sessions.first()


def get_current_quarter(school=None):
    if school and getattr(school, "current_quarter", None):
        return school.current_quarter

    current_term = Term.objects.filter(is_current=True)
    if school:
        current_term = current_term.filter(school=school)
    current_term = current_term.first()
    term_to_quarter = {
        "T1": "Q1",
        "T2": "Q2",
        "T3": "Q3",
        "T4": "Q4",
    }
    if current_term:
        return term_to_quarter.get(current_term.name, QUARTER_CHOICES[0][0])
    return QUARTER_CHOICES[0][0]


def build_quarter_sections(courses):
    sections = []
    courses_by_quarter = {
        quarter: list(courses.filter(quarter=quarter))
        for quarter, _label in QUARTER_CHOICES
    }

    for quarter, label in QUARTER_CHOICES:
        quarter_courses = courses_by_quarter[quarter]
        total_subjects = len(quarter_courses)
        total_marks = sum(course.total for course in quarter_courses)
        test_total = sum(course.get_test_average() for course in quarter_courses)
        average = round(total_marks / total_subjects, 2) if total_subjects else 0
        test_average = round(test_total / total_subjects, 2) if total_subjects else 0
        comment = PASS if average >= PASS_MARK and total_subjects else FAIL

        sections.append(
            {
                "code": quarter,
                "label": label,
                "courses": quarter_courses,
                "total_subjects": total_subjects,
                "test_average": test_average,
                "average": average,
                "comment": comment,
            }
        )

    return sections


def get_grade_for_average(average):
    for boundary, grade in GRADE_BOUNDARIES:
        if average >= Decimal(boundary):
            return grade
    return "NG"


def build_visible_grade_sections(quarter_sections, current_quarter):
    return [
        section
        for section in quarter_sections
        if section["code"] == current_quarter or section["total_subjects"] > 0
    ]


def build_final_report_summary(quarter_sections):
    quarter_count = len(QUARTER_CHOICES)
    recorded_sections = [
        section for section in quarter_sections if section["total_subjects"] > 0
    ]
    total_average = sum(Decimal(str(section["average"])) for section in quarter_sections)
    final_average = (total_average / Decimal(quarter_count)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    grade = get_grade_for_average(final_average)

    return {
        "average": final_average,
        "grade": grade,
        "comment": PASS if final_average >= Decimal(PASS_MARK) else FAIL,
        "quarter_count": quarter_count,
        "recorded_quarters": len(recorded_sections),
        "is_complete": len(recorded_sections) == quarter_count,
    }


def update_result_summary(student, session, quarter):
    school = student.student.school
    courses = TakenCourse.objects.filter(student=student, school=school, quarter=quarter)
    section = build_quarter_sections(courses)[["Q1", "Q2", "Q3", "Q4"].index(quarter)]
    defaults = {
        "total_subjects": section["total_subjects"],
        "total_points": 0,
        "average": section["average"],
        "comment": section["comment"],
    }

    results = Result.objects.filter(
        student=student,
        school=school,
        session=str(session) if session else "",
        quarter=quarter,
    )
    if results.exists():
        results.update(**defaults)
    else:
        Result.objects.create(
            student=student,
            school=school,
            session=str(session) if session else "",
            quarter=quarter,
            **defaults,
        )


def save_assessment_mark(student, course, quarter, field_name, mark, session=None):
    if field_name not in {"assignment", "mid_exam", "quiz", "attendance", "final_exam"}:
        return None

    taken_course, _created = TakenCourse.objects.get_or_create(
        student=student,
        course=course,
        school=student.student.school,
        quarter=quarter,
    )
    setattr(taken_course, field_name, mark)
    taken_course.save()
    update_result_summary(student, session or get_current_session(student.student.school), quarter)
    return taken_course


# =========================================================
# ADD SCORE
# =========================================================
@login_required
@lecturer_required
def add_score(request):
    current_session = get_current_session(getattr(request.user, "school", None))
    current_quarter = get_current_quarter(getattr(request.user, "school", None))

    if not current_session:
        messages.error(request, "No active session found.")
        return render(request, "result/add_score.html")


    courses = Course.objects.filter(
        Q(allocated_subjects__teacher=request.user) | Q(teacher=request.user),
        school=request.user.school,
    ).distinct()

    return render(
        request,
        "result/add_score.html",
        {
            "current_session": current_session,
            "current_semester": dict(QUARTER_CHOICES).get(current_quarter, "Quarter 1"),
            "current_quarter": current_quarter,
            "courses": courses,
        },
    )


# =========================================================
# ADD SCORE FOR COURSE
# =========================================================
@login_required
@lecturer_required
def add_score_for(request, id):
    current_session = get_current_session(getattr(request.user, "school", None))
    selected_quarter = request.GET.get("quarter") or get_current_quarter(getattr(request.user, "school", None))
    valid_quarters = dict(QUARTER_CHOICES)

    if selected_quarter not in valid_quarters:
        selected_quarter = get_current_quarter(getattr(request.user, "school", None))

    if not current_session:
        messages.error(request, "No active session found.")
        return HttpResponseRedirect(reverse_lazy("add_score"))

    courses = Course.objects.filter(
        Q(allocated_subjects__teacher=request.user) | Q(teacher=request.user),
        school=request.user.school,
    ).distinct()
    course = get_object_or_404(courses, pk=id)

    if course.class_assigned:
        for student in Student.objects.filter(student__school=request.user.school, student_class=course.class_assigned):
            TakenCourse.objects.get_or_create(
                student=student,
                course=course,
                school=request.user.school,
                quarter=selected_quarter,
            )

    if request.method == "GET":
        students = TakenCourse.objects.filter(
            school=request.user.school,
            course__id=id,
            quarter=selected_quarter,
        ).select_related("student__student", "course")

        return render(
            request,
            "result/add_score_for.html",
            {
                "title": "Submit Score",
                "courses": courses,
                "course": course,
                "students": students,
                "current_session": current_session,
                "current_quarter": selected_quarter,
                "quarters": QUARTER_CHOICES,
                "quarter_label": valid_quarters[selected_quarter],
            },
        )

    if request.method == "POST":
        ids = ()
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)

        for key in data.keys():
            ids = ids + (str(key),)

        for sid in ids:
            student = get_object_or_404(
                TakenCourse,
                id=sid,
                school=request.user.school,
                course=course,
                quarter=selected_quarter,
            )
            score = data.getlist(sid)
            if len(score) < 5:
                continue

            obj = student
            obj.assignment = score[0]
            obj.mid_exam = score[1]
            obj.quiz = score[2]
            obj.attendance = score[3]
            obj.final_exam = score[4]

            obj.total = obj.get_total()
            obj.grade = obj.get_grade()
            obj.point = obj.get_point()
            obj.comment = obj.get_comment()
            obj.save()

            update_result_summary(student.student, current_session, selected_quarter)

        messages.success(request, "Successfully Recorded!")
        return HttpResponseRedirect(
            f"{reverse_lazy('add_score_for', kwargs={'id': id})}?quarter={selected_quarter}"
        )


# =========================================================
# GRADE RESULT
# =========================================================
@login_required
@student_required
def grade_result(request):
    student = get_object_or_404(Student, student__pk=request.user.id, student__school=request.user.school)

    courses = TakenCourse.objects.filter(student=student, school=request.user.school)
    results = Result.objects.filter(student=student, school=request.user.school)
    quarter_sections = build_quarter_sections(courses)
    current_quarter = get_current_quarter(request.user.school)
    visible_quarter_sections = build_visible_grade_sections(quarter_sections, current_quarter)
    final_report = build_final_report_summary(quarter_sections)

    return render(
        request,
        "result/grade_results.html",
        {
            "courses": courses,
            "results": results,
            "student": student,
            "quarter_sections": quarter_sections,
            "visible_quarter_sections": visible_quarter_sections,
            "current_quarter": current_quarter,
            "final_report": final_report,
        },
    )


# =========================================================
# ASSESSMENT RESULT
# =========================================================
@login_required
@student_required
def assessment_result(request):
    student = get_object_or_404(Student, student__pk=request.user.id, student__school=request.user.school)

    courses = TakenCourse.objects.filter(student=student, school=request.user.school)
    result = Result.objects.filter(student=student, school=request.user.school)
    quarter_sections = build_quarter_sections(courses)
    
    # Get physical assessment marks for this student
    physical_assessments = PhysicalAssessmentMark.objects.filter(
        student=student
    ).select_related('assessment__subject', 'assessment').order_by(
        'assessment__subject__title', '-assessment__date_conducted'
    )
    
    # Group physical assessments by subject
    physical_assessments_by_subject = {}
    for mark in physical_assessments:
        subject_id = mark.assessment.subject_id
        if subject_id not in physical_assessments_by_subject:
            physical_assessments_by_subject[subject_id] = []
        physical_assessments_by_subject[subject_id].append(mark)

    return render(
        request,
        "result/assessment_results.html",
        {
            "courses": courses,
            "result": result,
            "student": student,
            "quarter_sections": quarter_sections,
            "physical_assessments_by_subject": physical_assessments_by_subject,
        },
    )


# =========================================================
# RESULT SHEET PDF
# =========================================================
@login_required
@lecturer_required
def result_sheet_pdf_view(request, id):
    current_session = get_current_session(getattr(request.user, "school", None))
    selected_quarter = request.GET.get("quarter") or get_current_quarter(getattr(request.user, "school", None))

    course = get_object_or_404(
        Course.objects.filter(
            school=request.user.school,
        ).filter(Q(allocated_subjects__teacher=request.user) | Q(teacher=request.user)).distinct(),
        id=id,
    )
    result = TakenCourse.objects.filter(school=request.user.school, course=course, quarter=selected_quarter)

    no_of_pass = result.filter(comment="PASS").count()
    no_of_fail = result.filter(comment="FAIL").count()

    fname = f"{current_session}_{selected_quarter}_{course}_resultSheet.pdf"
    fname = fname.replace("/", "-")

    os.makedirs(settings.MEDIA_ROOT + "/result_sheet", exist_ok=True)
    flocation = settings.MEDIA_ROOT + "/result_sheet/" + fname

    doc = SimpleDocTemplate(
        flocation,
        rightMargin=0,
        leftMargin=6.5 * CM,
        topMargin=0.3 * CM,
        bottomMargin=0,
    )

    styles = getSampleStyleSheet()
    Story = [Spacer(1, 0.2)]

    logo = settings.STATICFILES_DIRS[0] + "/img/brand.png"
    im = Image(logo, 1 * inch, 1 * inch)
    Story.append(im)

    title = Paragraph(
        f"<b>{current_session} {selected_quarter} Result Sheet</b>",
        styles["Normal"],
    )
    Story.append(title)
    Story.append(Spacer(1, 0.2 * inch))

    header = [("S/N", "ID NO.", "FULL NAME", "TEST AVG", "FINAL MARK", "GRADE", "COMMENT")]
    table_header = Table(header)
    table_header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.black),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    Story.append(table_header)

    count = 0
    for s in result:
        data = [
            (
                count + 1,
                s.student.student.username,
                s.student.student.get_full_name(),
                s.get_test_average(),
                s.total,
                s.grade,
                s.comment,
            )
        ]
        count += 1

        table = Table(data)
        table.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.black)]))
        Story.append(table)

    doc.build(Story)

    fs = FileSystemStorage(settings.MEDIA_ROOT + "/result_sheet")
    with fs.open(fname) as pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{fname}"'
        return response


# =========================================================
# STUDENT RESULT PDF
# =========================================================
@login_required
@student_required
def student_result_pdf_view(request):
    current_session = get_current_session(getattr(request.user, "school", None))
    student = get_object_or_404(Student, student=request.user, student__school=request.user.school)
    courses = TakenCourse.objects.filter(
        student=student,
        school=request.user.school,
    ).select_related("course").order_by("quarter", "course__title")
    quarter_sections = build_quarter_sections(courses)
    final_report = build_final_report_summary(quarter_sections)

    fname = f"{request.user.username}_results.pdf"
    os.makedirs(settings.MEDIA_ROOT + "/result_sheet", exist_ok=True)
    flocation = settings.MEDIA_ROOT + "/result_sheet/" + fname

    doc = SimpleDocTemplate(
        flocation,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("<b>Student Result Report</b>", styles["Title"]),
        Paragraph(f"Name: {request.user.get_full_name}", styles["Normal"]),
        Paragraph(f"Session: {current_session or ''}", styles["Normal"]),
        Paragraph(f"Level: {student.level or ''}", styles["Normal"]),
        Spacer(1, 0.2 * inch),
    ]

    for section in quarter_sections:
        story.append(Paragraph(f"<b>{section['label']}</b>", styles["Heading3"]))
        data = [["Subject", "Test Avg", "Exam", "Final Mark", "Grade", "Comment"]]

        for taken_course in section["courses"]:
            data.append([
                taken_course.course.title,
                taken_course.get_test_average(),
                taken_course.final_exam,
                taken_course.total,
                taken_course.grade,
                taken_course.comment,
            ])

        if len(data) == 1:
            data.append(["No result recorded", "", "", "", "", ""])

        data.append([
            "Quarter Summary",
            section["test_average"],
            "",
            section["average"],
            "",
            section["comment"],
        ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.black),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

    final_data = [
        ["Final Report Average", "Grade", "Comment", "Quarters Recorded"],
        [
            final_report["average"],
            final_report["grade"],
            final_report["comment"],
            f"{final_report['recorded_quarters']} of {final_report['quarter_count']}",
        ],
    ]
    final_table = Table(final_data, repeatRows=1)
    final_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(Paragraph("<b>Final Report</b>", styles["Heading3"]))
    story.append(final_table)

    doc.build(story)

    fs = FileSystemStorage(settings.MEDIA_ROOT + "/result_sheet")
    with fs.open(fname) as pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{fname}"'
        return response


# =========================================================
# COURSE REGISTRATION PDF
# =========================================================
@login_required
@student_required
def course_registration_form(request):
    current_session = get_current_session(getattr(request.user, "school", None))

    courses = TakenCourse.objects.filter(
        student__student__id=request.user.id,
        school=request.user.school,
    )

    student = Student.objects.get(student__pk=request.user.id, student__school=request.user.school)

    fname = request.user.username + ".pdf"
    os.makedirs(settings.MEDIA_ROOT + "/registration_form", exist_ok=True)
    flocation = settings.MEDIA_ROOT + "/registration_form/" + fname

    doc = SimpleDocTemplate(flocation)

    Story = [Spacer(1, 0.5)]

    title = Paragraph(
        "<b>COURSE REGISTRATION FORM</b>",
        getSampleStyleSheet()["Normal"],
    )
    Story.append(title)

    Story.append(
        Paragraph(f"Name: {request.user.get_full_name}", getSampleStyleSheet()["Normal"])
    )

    Story.append(
        Paragraph(f"Session: {current_session}", getSampleStyleSheet()["Normal"])
    )

    Story.append(Paragraph(f"Level: {student.level}", getSampleStyleSheet()["Normal"]))

    Story.append(Spacer(1, 0.5))

    for c in courses:
        Story.append(
            Paragraph(f"{c.course.code} - {c.course.title}", getSampleStyleSheet()["Normal"])
        )

    doc.build(Story)

    fs = FileSystemStorage(settings.MEDIA_ROOT + "/registration_form")
    with fs.open(fname) as pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{fname}"'
        return response


# =========================================================
# PHYSICAL ASSESSMENT VIEWS (FOR TEACHERS TO ENTER MARKS)
# =========================================================
from .models import PhysicalAssessment, PhysicalAssessmentMark
from .forms import PhysicalAssessmentForm, PhysicalAssessmentMarkEntryForm


@login_required
@lecturer_required
def physical_assessment_list(request):
    """
    List all physical assessments created by the logged-in teacher.
    """
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')

    # Get subjects taught by this teacher
    teacher_subjects = Course.objects.filter(
        Q(allocated_subjects__teacher=request.user) | Q(teacher=request.user),
        school=school,
    ).distinct()

    # Get assessments for these subjects
    assessments = PhysicalAssessment.objects.filter(
        subject__in=teacher_subjects,
        school=school,
    ).select_related('subject', 'created_by').order_by('-date_conducted', '-created_at')

    # Filter by subject if specified
    subject_id = request.GET.get('subject')
    if subject_id:
        assessments = assessments.filter(subject_id=subject_id)

    # Filter by assessment type if specified
    assessment_type = request.GET.get('type')
    if assessment_type:
        assessments = assessments.filter(assessment_type=assessment_type)

    return render(
        request,
        'result/physical_assessment_list.html',
        {
            'assessments': assessments,
            'subjects': teacher_subjects,
            'selected_subject': subject_id,
            'selected_type': assessment_type,
            'assessment_types': PhysicalAssessment.ASSESSMENT_TYPE_CHOICES,
        }
    )


@login_required
@lecturer_required
def physical_assessment_create(request):
    """
    Create a new physical assessment.
    """
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = PhysicalAssessmentForm(request.POST, school=school, teacher=request.user)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.school = school
            assessment.created_by = request.user
            assessment.save()
            messages.success(request, f"Assessment '{assessment.title}' created successfully.")
            return redirect('physical_assessment_enter_marks', assessment_id=assessment.id)
    else:
        form = PhysicalAssessmentForm(school=school, teacher=request.user)

    return render(
        request,
        'result/physical_assessment_form.html',
        {
            'form': form,
            'title': 'Create Physical Assessment',
        }
    )


@login_required
@lecturer_required
def physical_assessment_edit(request, assessment_id):
    """
    Edit an existing physical assessment.
    """
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')

    assessment = get_object_or_404(
        PhysicalAssessment,
        id=assessment_id,
        school=school,
    )

    # Check if teacher has permission to edit this assessment
    teacher_subjects = Course.objects.filter(
        Q(allocated_subjects__teacher=request.user) | Q(teacher=request.user),
        school=school,
    ).distinct()
    
    if assessment.subject not in teacher_subjects:
        messages.error(request, "You don't have permission to edit this assessment.")
        return redirect('physical_assessment_list')

    if request.method == 'POST':
        form = PhysicalAssessmentForm(request.POST, instance=assessment, school=school, teacher=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Assessment '{assessment.title}' updated successfully.")
            return redirect('physical_assessment_list')
    else:
        form = PhysicalAssessmentForm(instance=assessment, school=school, teacher=request.user)

    return render(
        request,
        'result/physical_assessment_form.html',
        {
            'form': form,
            'title': 'Edit Physical Assessment',
            'assessment': assessment,
        }
    )


@login_required
@lecturer_required
def physical_assessment_delete(request, assessment_id):
    """
    Delete a physical assessment.
    """
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')

    assessment = get_object_or_404(
        PhysicalAssessment,
        id=assessment_id,
        school=school,
    )

    # Check if teacher has permission to delete this assessment
    teacher_subjects = Course.objects.filter(
        Q(allocated_subjects__teacher=request.user) | Q(teacher=request.user),
        school=school,
    ).distinct()
    
    if assessment.subject not in teacher_subjects:
        messages.error(request, "You don't have permission to delete this assessment.")
        return redirect('physical_assessment_list')

    if request.method == 'POST':
        title = assessment.title
        assessment.delete()
        messages.success(request, f"Assessment '{title}' deleted successfully.")
        return redirect('physical_assessment_list')

    return render(
        request,
        'result/physical_assessment_confirm_delete.html',
        {'assessment': assessment}
    )


@login_required
@lecturer_required
def physical_assessment_enter_marks(request, assessment_id):
    """
    Enter marks for all students in a physical assessment.
    """
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')

    assessment = get_object_or_404(
        PhysicalAssessment,
        id=assessment_id,
        school=school,
    )

    # Check if teacher has permission to enter marks for this assessment
    teacher_subjects = Course.objects.filter(
        Q(allocated_subjects__teacher=request.user) | Q(teacher=request.user),
        school=school,
    ).distinct()
    
    if assessment.subject not in teacher_subjects:
        messages.error(request, "You don't have permission to enter marks for this assessment.")
        return redirect('physical_assessment_list')

    # Get all students in the class for this subject
    if assessment.subject.class_assigned:
        students = Student.objects.filter(
            student__school=school,
            student_class=assessment.subject.class_assigned,
        ).select_related('student')
    else:
        # If no class assigned, get all students in the school
        students = Student.objects.filter(
            student__school=school,
        ).select_related('student')

    # Get existing marks
    existing_marks = {
        m.student_id: m 
        for m in PhysicalAssessmentMark.objects.filter(assessment=assessment)
    }

    if request.method == 'POST':
        saved_count = 0
        for student in students:
            mark_key = f'mark_{student.id}'
            remarks_key = f'remarks_{student.id}'
            
            if mark_key in request.POST:
                mark_value = request.POST.get(mark_key)
                remarks = request.POST.get(remarks_key, '')
                
                if mark_value:
                    mark, created = PhysicalAssessmentMark.objects.update_or_create(
                        assessment=assessment,
                        student=student,
                        defaults={
                            'marks_obtained': Decimal(mark_value),
                            'remarks': remarks,
                            'entered_by': request.user,
                        }
                    )
                    saved_count += 1

        messages.success(request, f"Marks saved for {saved_count} student(s).")
        return redirect('physical_assessment_view_marks', assessment_id=assessment.id)

    # Prepare student data with existing marks
    student_data = []
    for student in students:
        mark = existing_marks.get(student.id)
        student_data.append({
            'student': student,
            'mark': mark.marks_obtained if mark else '',
            'remarks': mark.remarks if mark else '',
            'percentage': mark.percentage if mark else 0,
        })

    return render(
        request,
        'result/physical_assessment_mark_entry.html',
        {
            'assessment': assessment,
            'student_data': student_data,
            'max_marks': assessment.max_marks,
        }
    )


@login_required
@lecturer_required
def physical_assessment_view_marks(request, assessment_id):
    """
    View all marks for a physical assessment.
    """
    school = getattr(request.user, 'school', None)
    if not school:
        messages.error(request, "No school associated with your account.")
        return redirect('dashboard')

    assessment = get_object_or_404(
        PhysicalAssessment,
        id=assessment_id,
        school=school,
    )

    # Check if teacher has permission to view this assessment
    teacher_subjects = Course.objects.filter(
        Q(allocated_subjects__teacher=request.user) | Q(teacher=request.user),
        school=school,
    ).distinct()
    
    if assessment.subject not in teacher_subjects and not request.user.is_superuser:
        messages.error(request, "You don't have permission to view this assessment.")
        return redirect('physical_assessment_list')

    # Get all marks for this assessment
    marks = PhysicalAssessmentMark.objects.filter(
        assessment=assessment,
    ).select_related('student__student').order_by('student__student__last_name')

    # Calculate statistics
    total_students = marks.count()
    if total_students > 0:
        total_marks = sum(m.marks_obtained for m in marks)
        average_marks = total_marks / total_students
        highest_mark = max(m.marks_obtained for m in marks)
        lowest_mark = min(m.marks_obtained for m in marks)
        pass_count = sum(1 for m in marks if m.marks_obtained >= (assessment.max_marks * Decimal('0.5')))
    else:
        average_marks = highest_mark = lowest_mark = 0
        pass_count = 0

    return render(
        request,
        'result/physical_assessment_view_marks.html',
        {
            'assessment': assessment,
            'marks': marks,
            'statistics': {
                'total_students': total_students,
                'average_marks': round(average_marks, 2),
                'highest_mark': highest_mark,
                'lowest_mark': lowest_mark,
                'pass_count': pass_count,
                'fail_count': total_students - pass_count,
            }
        }
    )