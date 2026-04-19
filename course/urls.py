from django.urls import path
from . import views


urlpatterns = [

    # Course urls
    path("course/<slug>/detail/", views.course_single, name="course_detail"),
    path("<int:pk>/course/add/", views.subject_add_view, name="course_add"),
    path("course/<slug>/edit/", views.course_edit, name="edit_course"),
    path("course/delete/<slug>/", views.subject_delete_view, name="delete_course"),
    path("course/registration/", views.course_registration, name="course_registration"),
    path("course/drop/", views.course_drop, name="course_drop"),
    path("my_courses/", views.user_course_list, name="user_course_list"),
    path("students/<int:student_id>/assign-class/", views.assign_class_view, name="assign_class_view"),


    # File uploads urls
    path(
        "course/<slug>/documentations/upload/",
        views.handle_file_upload,
        name="upload_file_view",
    ),
    path(
        "course/<slug>/documentations/<int:file_id>/edit/",
        views.handle_file_edit,
        name="upload_file_edit",
    ),
    path(
        "course/<slug>/documentations/<int:file_id>/delete/",
        views.handle_file_delete,
        name="upload_file_delete",
    ),
    # Video uploads urls
    path(
        "course/<slug>/video_tutorials/upload/",
        views.handle_video_upload,
        name="upload_video",
    ),
    path(
        "course/<slug>/video_tutorials/<video_slug>/detail/",
        views.handle_video_single,
        name="video_single",
    ),
    path(
        "course/<slug>/video_tutorials/<video_slug>/edit/",
        views.handle_video_edit,
        name="upload_video_edit",
    ),
    path(
        "course/<slug>/video_tutorials/<video_slug>/delete/",
        views.handle_video_delete,
        name="upload_video_delete",
    ),

]
