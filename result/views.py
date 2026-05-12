import os

from django.shortcuts import render, get_object_or_404
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
from .models import PASS, FAIL, QUARTER_CHOICES, TakenCourse, Result


CM = 2.54
PASS_MARK = 45


def get_current_session():
    return Session.objects.filter(is_current=True).first()


def get_current_quarter():
    current_term = Term.objects.filter(is_current=True).first()
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


def update_result_summary(student, session, quarter):
    courses = TakenCourse.objects.filter(student=student, quarter=quarter)
    section = build_quarter_sections(courses)[["Q1", "Q2", "Q3", "Q4"].index(quarter)]
    defaults = {
        "total_subjects": section["total_subjects"],
        "total_points": 0,
        "average": section["average"],
        "comment": section["comment"],
    }

    results = Result.objects.filter(
        student=student,
        session=str(session) if session else "",
        quarter=quarter,
    )
    if results.exists():
        results.update(**defaults)
    else:
        Result.objects.create(
            student=student,
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
        quarter=quarter,
    )
    setattr(taken_course, field_name, mark)
    taken_course.save()
    update_result_summary(student, session or get_current_session(), quarter)
    return taken_course


# =========================================================
# ADD SCORE
# =========================================================
@login_required
@lecturer_required
def add_score(request):
    current_session = get_current_session()
    current_quarter = get_current_quarter()

    if not current_session:
        messages.error(request, "No active session found.")
        return render(request, "result/add_score.html")


    courses = Course.objects.filter(
        Q(allocated_subjects__teacher=request.user) | Q(teacher=request.user)
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
    current_session = get_current_session()
    selected_quarter = request.GET.get("quarter") or get_current_quarter()
    valid_quarters = dict(QUARTER_CHOICES)

    if selected_quarter not in valid_quarters:
        selected_quarter = get_current_quarter()

    if not current_session:
        messages.error(request, "No active session found.")
        return HttpResponseRedirect(reverse_lazy("add_score"))

    courses = Course.objects.filter(
        Q(allocated_subjects__teacher=request.user) | Q(teacher=request.user)
    ).distinct()
    course = get_object_or_404(Course, pk=id)

    if course.class_assigned:
        for student in Student.objects.filter(student_class=course.class_assigned):
            TakenCourse.objects.get_or_create(
                student=student,
                course=course,
                quarter=selected_quarter,
            )

    if request.method == "GET":
        students = TakenCourse.objects.filter(
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
            student = TakenCourse.objects.get(id=sid, quarter=selected_quarter)
            score = data.getlist(sid)
            if len(score) < 5:
                continue

            obj = TakenCourse.objects.get(pk=sid, quarter=selected_quarter)
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
    student = Student.objects.get(student__pk=request.user.id)

    courses = TakenCourse.objects.filter(student__student__pk=request.user.id)
    results = Result.objects.filter(student__student__pk=request.user.id)
    quarter_sections = build_quarter_sections(courses)

    return render(
        request,
        "result/grade_results.html",
        {
            "courses": courses,
            "results": results,
            "student": student,
            "quarter_sections": quarter_sections,
        },
    )


# =========================================================
# ASSESSMENT RESULT
# =========================================================
@login_required
@student_required
def assessment_result(request):
    student = Student.objects.get(student__pk=request.user.id)

    courses = TakenCourse.objects.filter(student__student__pk=request.user.id)
    result = Result.objects.filter(student__student__pk=request.user.id)
    quarter_sections = build_quarter_sections(courses)

    return render(
        request,
        "result/assessment_results.html",
        {
            "courses": courses,
            "result": result,
            "student": student,
            "quarter_sections": quarter_sections,
        },
    )


# =========================================================
# RESULT SHEET PDF
# =========================================================
@login_required
@lecturer_required
def result_sheet_pdf_view(request, id):
    current_session = get_current_session()
    selected_quarter = request.GET.get("quarter") or get_current_quarter()

    result = TakenCourse.objects.filter(course__pk=id, quarter=selected_quarter)
    course = get_object_or_404(Course, id=id)

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
    current_session = get_current_session()
    student = get_object_or_404(Student, student=request.user)
    courses = TakenCourse.objects.filter(
        student=student
    ).select_related("course").order_by("quarter", "course__title")
    quarter_sections = build_quarter_sections(courses)

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
    current_session = get_current_session()

    courses = TakenCourse.objects.filter(
        student__student__id=request.user.id
    )

    student = Student.objects.get(student__pk=request.user.id)

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
