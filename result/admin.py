from django.contrib import admin
from django.contrib.auth.models import Group

from .models import TakenCourse, Result


class ScoreAdmin(admin.ModelAdmin):
    list_display = [
        "student",
<<<<<<< HEAD
        "school",
=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
        "course",
        "quarter",
        "assignment",
        "mid_exam",
        "quiz",
        "attendance",
        "final_exam",
        "test_average",
        "total",
        "grade",
        "comment",
    ]
<<<<<<< HEAD
    list_filter = ("school", "quarter", "course")
    search_fields = ("student__student__first_name", "student__student__last_name", "course__title")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(school=getattr(request.user, "school_id", None))

    def save_model(self, request, obj, form, change):
        if not obj.school_id:
            obj.school = getattr(request.user, "school", None)
        super().save_model(request, obj, form, change)
=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e

    @admin.display(description="Tests Avg")
    def test_average(self, obj):
        return obj.get_test_average()


admin.site.register(TakenCourse, ScoreAdmin)
<<<<<<< HEAD
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "school", "session", "quarter", "average", "comment")
    list_filter = ("school", "session", "quarter", "comment")
    search_fields = ("student__student__first_name", "student__student__last_name")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(school=getattr(request.user, "school_id", None))

    def save_model(self, request, obj, form, change):
        if not obj.school_id:
            obj.school = getattr(request.user, "school", None)
        super().save_model(request, obj, form, change)


admin.site.register(Result, ResultAdmin)
=======
admin.site.register(Result)
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
