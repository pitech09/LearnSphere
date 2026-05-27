from django.urls import path
from . import views

urlpatterns = [

    # Course urls
    path("class/<int:class_id>/course/<slug:subject_slug>/detail/", views.course_single, name="course_detail"),
    path("class/<int:class_id>/course/<slug:subject_slug>/edit/", views.course_edit, name="edit_course"),
    path("class/<int:class_id>/course/<slug:subject_slug>/delete/", views.subject_delete, name="delete_course"),
    path("class/<int:class_id>/course/add/", views.subject_add_view, name="course_add"),   # if you need class_id when adding, else keep as is
    path("course/registration/", views.course_registration, name="course_registration"),
    path("course/drop/", views.course_drop, name="course_drop"),
    path("my_courses/", views.user_course_list, name="user_course_list"),
    path("students/<int:student_id>/assign-class/", views.assign_class_view, name="assign_class_view"),

    # File uploads urls
    path("class/<int:class_id>/course/<slug:subject_slug>/documentations/upload/",
         views.handle_file_upload, name="upload_file_view"),
    path("class/<int:class_id>/course/<slug:subject_slug>/documentations/<int:file_id>/edit/",
         views.handle_file_edit, name="upload_file_edit"),
    path("class/<int:class_id>/course/<slug:subject_slug>/documentations/<int:file_id>/delete/",
         views.handle_file_delete, name="upload_file_delete"),

    # Video uploads urls
    path("class/<int:class_id>/course/<slug:subject_slug>/video_tutorials/upload/",
         views.handle_video_upload, name="upload_video"),
    path("class/<int:class_id>/course/<slug:subject_slug>/video_tutorials/<slug:video_slug>/detail/",
         views.handle_video_single, name="video_single"),
    path("class/<int:class_id>/course/<slug:subject_slug>/video_tutorials/<slug:video_slug>/edit/",
         views.handle_video_edit, name="upload_video_edit"),
    path("class/<int:class_id>/course/<slug:subject_slug>/video_tutorials/<slug:video_slug>/delete/",
         views.handle_video_delete, name="upload_video_delete"),

]