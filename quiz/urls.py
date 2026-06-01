from django.urls import path
from . import views

urlpatterns = [
    # Quiz list for a specific subject (using class + subject slug)
    path("class/<int:class_id>/course/<slug:subject_slug>/quizzes/", views.quiz_list, name="quiz_index"),

    path("progress/", view=views.QuizUserProgressView.as_view(), name="quiz_progress"),
    path("ready/", views.ready_assessments, name="ready_assessments"),
    path("result/<int:sitting_id>/", views.assessment_result_detail, name="assessment_result_detail"),
    path("class/<int:class_id>/course/<slug:subject_slug>/physical-test/add/", views.physical_test_create, name="physical_test_create"),
    path("test/<int:quiz_id>/marks/", views.test_mark_entry, name="test_mark_entry"),
    path("marking_list/", view=views.QuizMarkingList.as_view(), name="quiz_marking"),
    path("marking/<int:pk>/", view=views.QuizMarkingDetail.as_view(), name="quiz_marking_detail"),

    # Take a quiz – requires quiz primary key and subject identifiers
    path("class/<int:class_id>/course/<slug:subject_slug>/quiz/<int:pk>/take/", views.QuizTake.as_view(), name="quiz_take"),

    # Create a new quiz (subject identified by class + slug)
    path("class/<int:class_id>/course/<slug:subject_slug>/quiz_add/", views.QuizCreateView.as_view(), name="quiz_create"),

    # Edit / delete a specific quiz (quiz pk + subject identifiers)
    path("class/<int:class_id>/course/<slug:subject_slug>/quiz/<int:pk>/edit/", views.QuizUpdateView.as_view(), name="quiz_update"),
    path("class/<int:class_id>/course/<slug:subject_slug>/quiz/<int:pk>/delete/", views.quiz_delete, name="quiz_delete"),

    # Add multiple‑choice or essay question to a quiz
    path("class/<int:class_id>/course/<slug:subject_slug>/quiz/<int:quiz_id>/mc-question/add/", views.MCQuestionCreate.as_view(), name="mc_create"),
    path("class/<int:class_id>/course/<slug:subject_slug>/quiz/<int:quiz_id>/essay-question/add/", views.EssayQuestionCreate.as_view(), name="essay_create"),
]
