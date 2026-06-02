from django.urls import path

from django.views.i18n import JavaScriptCatalog

from .views import (
    health_check_view,
    profile,
    profile_single,
    admin_panel,
    profile_update,
    change_password,
    LecturerFilterView,
    StudentListView,
    staff_add_view,
    edit_staff,
    delete_staff,
    student_add_view,
    edit_student,
    delete_student,
    ParentAdd,
    validate_username,
    register,
    school_signup,
    render_lecturer_pdf_list,
    render_student_pdf_list,
    custom_login_view,
    logout_view,
    sms_password_reset,
    sms_password_reset_done,
    sms_password_reset_confirm,
    sms_password_reset_complete,
    parent_list_view,
)

urlpatterns = [
    # Authentication
    path("login/", custom_login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Password Reset via SMS
    path("password-reset/", sms_password_reset, name="password_reset"),
    path("password-reset/done/", sms_password_reset_done, name="password_reset_done"),
    path("reset/<uidb64>/<token>/", sms_password_reset_confirm, name="password_reset_confirm"),
    path("reset/done/", sms_password_reset_complete, name="password_reset_complete"),

    # Dashboard / Profile
    path("admin_panel/", admin_panel, name="admin_panel"),
    path("profile/", profile, name="profile"),

    path(
        "profile/<int:user_id>/detail/",
        profile_single,
        name="profile_single",
    ),

    path("setting/", profile_update, name="edit_profile"),
    path("change_password/", change_password, name="change_password"),

    # Lecturers
    path("lecturers/", LecturerFilterView.as_view(), name="lecturer_list"),
    path("lecturer/add/", staff_add_view, name="add_lecturer"),
    path("staff/<int:pk>/edit/", edit_staff, name="staff_edit"),
    path(
        "lecturers/<int:pk>/delete/",
        delete_staff,
        name="lecturer_delete",
    ),

    # Students
    path("students/", StudentListView.as_view(), name="student_list"),
    path("student/add/", student_add_view, name="add_student"),
    path("student/<int:pk>/edit/", edit_student, name="student_edit"),
    path(
        "students/<int:pk>/delete/",
        delete_student,
        name="student_delete",
    ),

    # Parents
    path("parents/", parent_list_view, name="parent_list"),
    path("parents/add/", ParentAdd.as_view(), name="add_parent"),

    # AJAX
    path(
        "ajax/validate-username/",
        validate_username,
        name="validate_username",
    ),

    # Registration
    path("register/", register, name="register"),
    path("schools/signup/", school_signup, name="school_signup"),

    # Health
    path("health/", health_check_view, name="health_check_view"),

    # PDFs
    path(
        "create_lecturers_pdf_list/",
        render_lecturer_pdf_list,
        name="lecturer_list_pdf",
    ),

    path(
        "create_students_pdf_list/",
        render_student_pdf_list,
        name="student_list_pdf",
    ),

    # i18n JS
    path(
        "jsi18n/",
        JavaScriptCatalog.as_view(),
        name="javascript-catalog",
    ),
]