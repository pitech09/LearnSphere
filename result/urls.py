from django.urls import path
from .views import (
    add_score,
    add_score_for,
    grade_result,
    assessment_result,
    course_registration_form,
    result_sheet_pdf_view,
    student_result_pdf_view,
    # Physical assessment views
    physical_assessment_list,
    physical_assessment_create,
    physical_assessment_edit,
    physical_assessment_delete,
    physical_assessment_enter_marks,
    physical_assessment_view_marks,
)


urlpatterns = [
    path("manage-score/", add_score, name="add_score"),
    path("manage-score/<int:id>/", add_score_for, name="add_score_for"),
    path("grade/", grade_result, name="grade_results"),
    path("assessment/", assessment_result, name="ass_results"),
    path("result/print/<int:id>/", result_sheet_pdf_view, name="result_sheet_pdf_view"),
    path("result/print/", student_result_pdf_view, name="student_result_pdf_view"),
    path(
        "registration/form/", course_registration_form, name="course_registration_form"
    ),
    # Physical assessment URLs
    path("physical-assessments/", physical_assessment_list, name="physical_assessment_list"),
    path("physical-assessments/create/", physical_assessment_create, name="physical_assessment_create"),
    path("physical-assessments/<int:assessment_id>/edit/", physical_assessment_edit, name="physical_assessment_edit"),
    path("physical-assessments/<int:assessment_id>/delete/", physical_assessment_delete, name="physical_assessment_delete"),
    path("physical-assessments/<int:assessment_id>/enter-marks/", physical_assessment_enter_marks, name="physical_assessment_enter_marks"),
    path("physical-assessments/<int:assessment_id>/view-marks/", physical_assessment_view_marks, name="physical_assessment_view_marks"),
]
