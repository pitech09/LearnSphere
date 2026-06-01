from django.urls import path
from django.views.generic import TemplateView

from quiz import views

# Core app views
from .views import (
    bulk_fee_add,
    get_subjects_by_class,
    home_view,
    mark_entry_by_level,
    post_add,
    edit_post,
    delete_post,
    save_marks,
    session_list_view,
    session_add_view,
    session_update_view,
    session_delete_view,
    dashboard_view,
    principal_dashboard,
    teacher_dashboard,
    student_dashboard,
    current_quarter_update,
    platform_owner_dashboard,
    platform_school_reactivate,
    platform_school_suspend,
    platform_school_update,
    platform_suspend_overdue_schools,
    platform_schools_dashboard,
    class_list_view,
    class_add_view,
    class_update_view,
    class_delete_view,
    subject_list_view,
    subject_add_view,
    subject_update_view,
    subject_delete_view,
    fee_add,
    fee_edit,
    fee_delete,
    fee_list,
    fee_detail,
    payment_add,
    exam_list,
    exam_add,
    exam_edit,
    exam_delete,
    exam_detail,
    timetable_add,
    timetable_delete,
    timetable_edit,
    timetable_list,
    auto_generate_timetable,
    class_timetable_print
)

# Course app views (for URLs that use class_id + subject_slug)
from course.views import (
    course_single,
    course_edit,
    subject_delete,
    handle_file_upload,
    handle_file_edit,
    handle_file_delete,
    handle_video_upload,
    handle_video_single,
    handle_video_edit,
    handle_video_delete,
    course_registration,
    course_drop,
    user_course_list,
    assign_class_view,
)


urlpatterns = [
    # Accounts url
    path("", home_view, name="home"),
    path("add_item/", post_add, name="add_item"),
    path("item/<int:pk>/edit/", edit_post, name="edit_post"),
    path("item/<int:pk>/delete/", delete_post, name="delete_post"),

    # Session URLs
    path("session/", session_list_view, name="session_list"),
    path("session/add/", session_add_view, name="add_session"),
    path("session/<int:pk>/edit/", session_update_view, name="edit_session"),
    path("session/<int:pk>/delete/", session_delete_view, name="delete_session"),

    # Dashboard URLs
    path("dashboard/", dashboard_view, name="dashboard"),
    path("dashboard/principal/", principal_dashboard, name="principal_dashboard"),
    path("dashboard/teacher/", teacher_dashboard, name="teacher_dashboard"),
    path("dashboard/student/", student_dashboard, name="student_dashboard"),
    path("dashboard/platform/", platform_owner_dashboard, name="platform_owner_dashboard"),
    path("dashboard/schools/", platform_schools_dashboard, name="platform_schools_dashboard"),
    path("dashboard/schools/<int:pk>/", platform_school_update, name="platform_school_update"),
    path("dashboard/schools/<int:pk>/suspend/", platform_school_suspend, name="platform_school_suspend"),
    path("dashboard/schools/<int:pk>/reactivate/", platform_school_reactivate, name="platform_school_reactivate"),
    path("dashboard/schools/suspend-overdue/", platform_suspend_overdue_schools, name="platform_suspend_overdue_schools"),
    path("settings/current-quarter/", current_quarter_update, name="current_quarter_update"),

    # Class URLs
    path("class/", class_list_view, name="class_list"),
    path("class/add/", class_add_view, name="add_class"),
    path("class/<int:pk>/edit/", class_update_view, name="edit_class"),
    path("class/<int:pk>/delete/", class_delete_view, name="delete_class"),

    # Subject (old) URLs – keep for compatibility
    path('subjects/', subject_list_view, name='subject_list_view'),
    path('add_subject/', subject_add_view, name='add_subject_view'),
    path('edit_subject/<int:pk>', subject_update_view, name='edit_subject_view'),
    path('delete_subject/<int:pk>', subject_delete_view, name='delete_subject_view'),

    # Course (new) URLs using class_id and subject_slug (from course.views)
    path("class/<int:class_id>/course/<slug:subject_slug>/detail/", course_single, name="course_detail"),
    path("class/<int:class_id>/course/<slug:subject_slug>/edit/", course_edit, name="edit_course"),
    path("class/<int:class_id>/course/<slug:subject_slug>/delete/", subject_delete, name="delete_course"),
    path("course/registration/", course_registration, name="course_registration"),
    path("course/drop/", course_drop, name="course_drop"),
    path("my_courses/", user_course_list, name="user_course_list"),
    path("students/<int:student_id>/assign-class/", assign_class_view, name="assign_class_view"),

    # File upload URLs (new)
    path("class/<int:class_id>/course/<slug:subject_slug>/documentations/upload/",
         handle_file_upload, name="upload_file_view"),
    path("class/<int:class_id>/course/<slug:subject_slug>/documentations/<int:file_id>/edit/",
         handle_file_edit, name="upload_file_edit"),
    path("class/<int:class_id>/course/<slug:subject_slug>/documentations/<int:file_id>/delete/",
         handle_file_delete, name="upload_file_delete"),

    # Video upload URLs (new)
    path("class/<int:class_id>/course/<slug:subject_slug>/video_tutorials/upload/",
         handle_video_upload, name="upload_video"),
    path("class/<int:class_id>/course/<slug:subject_slug>/video_tutorials/<slug:video_slug>/detail/",
         handle_video_single, name="video_single"),
    path("class/<int:class_id>/course/<slug:subject_slug>/video_tutorials/<slug:video_slug>/edit/",
         handle_video_edit, name="upload_video_edit"),
    path("class/<int:class_id>/course/<slug:subject_slug>/video_tutorials/<slug:video_slug>/delete/",
         handle_video_delete, name="upload_video_delete"),

    # Fee URLs
    path('fees/', fee_list, name='fee_list'),
    path('fees/add/', fee_add, name='fee_add'),
    path('fees/<int:pk>/edit/', fee_edit, name='fee_edit'),
    path('fees/<int:pk>/delete/', fee_delete, name='fee_delete'),
    path('fees/<int:pk>/', fee_detail, name='fee_detail'),
    path('fees/<int:fee_pk>/pay/', payment_add, name='payment_add'),
    path('fees/bulk-add/', bulk_fee_add, name='bulk_fee_add'),

    path('exams/', exam_list, name='exam_list'),
    path('exams/add/', exam_add, name='exam_add'),
    path('exams/<int:pk>/edit/', exam_edit, name='exam_edit'),
    path('exams/<int:pk>/delete/', exam_delete, name='exam_delete'),
    path('exams/<int:pk>/', exam_detail, name='exam_detail'),

    path('timetable/', timetable_list, name='timetable_list'),
    path('timetable/add/', timetable_add, name='timetable_add'),
    path('timetable/<int:pk>/edit/', timetable_edit, name='timetable_edit'),
    path('timetable/<int:pk>/delete/', timetable_delete, name='timetable_delete'),
    path('timetable/auto-generate/', auto_generate_timetable, name='auto_generate_timetable'),
    path('timetable/class/<int:class_id>/print/', class_timetable_print, name='class_timetable_print'),

    path('marks/entry/', mark_entry_by_level, name='mark_entry_by_level'),
    path('marks/save/', save_marks, name='save_marks'),
    path('api/subjects-by-class/', get_subjects_by_class, name='get_subjects_by_class'),    # Legal page


    path("legal/", TemplateView.as_view(template_name="legal/privacy_terms.html"), name="legal"),
]