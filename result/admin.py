from django.contrib import admin
from django.contrib.auth.models import Group

from .models import TakenCourse, Result


class ScoreAdmin(admin.ModelAdmin):
    list_display = [
        "student",
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
    list_filter = ("school", "quarter", "course")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(school=getattr(request.user, "school_id", None))

    def save_model(self, request, obj, form, change):
        if not obj.school_id:
            obj.school = getattr(request.user, "school", None)
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        school_id = getattr(request.user, "school_id", None)
        if not (request.user.is_superuser and not school_id):
            if db_field.name == "school":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(pk=school_id)
            elif db_field.name == "student":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(student__school_id=school_id)
            elif db_field.name == "course":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(school_id=school_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description="Tests Avg")
    def test_average(self, obj):
        return obj.get_test_average()


admin.site.register(TakenCourse, ScoreAdmin)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "school", "session", "quarter", "total_subjects", "average", "comment")
    list_filter = ("school", "session", "quarter")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(school=getattr(request.user, "school_id", None))

    def save_model(self, request, obj, form, change):
        if not obj.school_id:
            obj.school = getattr(request.user, "school", None)
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        school_id = getattr(request.user, "school_id", None)
        if not (request.user.is_superuser and not school_id):
            if db_field.name == "school":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(pk=school_id)
            elif db_field.name == "student":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(student__school_id=school_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Result, ResultAdmin)
