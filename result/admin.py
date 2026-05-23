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

    @admin.display(description="Tests Avg")
    def test_average(self, obj):
        return obj.get_test_average()


admin.site.register(TakenCourse, ScoreAdmin)
admin.site.register(Result)
