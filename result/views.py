from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage

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

from core.models import Session
from course.models import Subject as Course
from accounts.models import Student
from accounts.decorators import lecturer_required, student_required
from .models import TakenCourse, Result


CM = 2.54


# =========================================================
# ADD SCORE
# =========================================================
@login_required
@lecturer_required
def add_score(request):
    current_session = Session.objects.filter(is_current=True).first()

    if not current_session:
        messages.error(request, "No active session found.")
        return render(request, "result/add_score.html")


    courses = Course.objects.filter(
        allocated_subjects__teacher=request.user
    ).distinct()    

    return render(
        request,
        "result/add_score.html",
        {
            "current_session": current_session,
            "courses": courses,
        },
    )


# =========================================================
# ADD SCORE FOR COURSE
# =========================================================
@login_required
@lecturer_required
def add_score_for(request, id):
    current_session = Session.objects.get(is_current_session=True)

    if request.method == "GET":
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=request.user.id
        )

        course = Course.objects.get(pk=id)

        students = TakenCourse.objects.filter(course__id=id)

        return render(
            request,
            "result/add_score_for.html",
            {
                "title": "Submit Score",
                "courses": courses,
                "course": course,
                "students": students,
                "current_session": current_session,
            },
        )

    if request.method == "POST":
        ids = ()
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)

        for key in data.keys():
            ids = ids + (str(key),)

        for sid in ids:
            student = TakenCourse.objects.get(id=sid)
            score = data.getlist(sid)

            obj = TakenCourse.objects.get(pk=sid)
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

            gpa = obj.calculate_gpa()
            cgpa = obj.calculate_cgpa()

            Result.objects.update_or_create(
                student=student.student,
                session=current_session,
                defaults={
                    "gpa": gpa,
                    "cgpa": cgpa,
                    "level": student.student.level,
                },
            )

        messages.success(request, "Successfully Recorded!")
        return HttpResponseRedirect(
            reverse_lazy("add_score_for", kwargs={"id": id})
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

    return render(
        request,
        "result/grade_results.html",
        {
            "courses": courses,
            "results": results,
            "student": student,
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

    return render(
        request,
        "result/assessment_results.html",
        {
            "courses": courses,
            "result": result,
            "student": student,
        },
    )


# =========================================================
# RESULT SHEET PDF
# =========================================================
@login_required
@lecturer_required
def result_sheet_pdf_view(request, id):
    current_session = Session.objects.get(is_current_session=True)

    result = TakenCourse.objects.filter(course__pk=id)
    course = get_object_or_404(Course, id=id)

    no_of_pass = result.filter(comment="PASS").count()
    no_of_fail = result.filter(comment="FAIL").count()

    fname = f"{current_session}_{course}_resultSheet.pdf"
    fname = fname.replace("/", "-")

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
        f"<b>{current_session} Result Sheet</b>",
        styles["Normal"],
    )
    Story.append(title)
    Story.append(Spacer(1, 0.2 * inch))

    header = [("S/N", "ID NO.", "FULL NAME", "TOTAL", "GRADE", "POINT", "COMMENT")]
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
                s.total,
                s.grade,
                s.point,
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
# COURSE REGISTRATION PDF
# =========================================================
@login_required
@student_required
def course_registration_form(request):
    current_session = Session.objects.get(is_current_session=True)

    courses = TakenCourse.objects.filter(
        student__student__id=request.user.id
    )

    student = Student.objects.get(student__pk=request.user.id)

    fname = request.user.username + ".pdf"
    flocation = settings.MEDIA_ROOT + "/registration_form/" + fname

    doc = SimpleDocTemplate(flocation)

    Story = [Spacer(1, 0.5)]

    title = Paragraph(
        "<b>COURSE REGISTRATION FORM</b>",
        getSampleStyleSheet()["Normal"],
    )
    Story.append(title)

    Story.append(
        Paragraph(f"Name: {request.user.get_full_name()}", getSampleStyleSheet()["Normal"])
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