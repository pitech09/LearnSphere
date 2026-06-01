from django.urls import path
from . import views

urlpatterns = [
    path("", views.parent_dashboard, name="parent_dashboard"),
    path("child/<int:student_id>/", views.parent_child_detail, name="parent_child_detail"),
    path("child/<int:student_id>/grades/", views.parent_grade_reports, name="parent_grade_reports"),
    path("announcements/", views.parent_announcements, name="parent_announcements"),
    path("fees/", views.parent_fees, name="parent_fees"),
    path("fees/<int:student_id>/", views.parent_fees, name="parent_fees_student"),
]