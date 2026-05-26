from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _
from django.contrib import admin

from .models import (
    Quiz,
    Progress,
    Question,
    MCQuestion,
    Choice,
    EssayQuestion,
    QuestionGrade,
    Sitting,
)


class ChoiceInline(admin.TabularInline):
    model = Choice


class QuizAdminForm(admin.ModelAdmin):
    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label=_("Questions"),
        widget=FilteredSelectMultiple(verbose_name=_("Questions"), is_stacked=False),
    )

    class Meta:
        model = Quiz
        fields = ["title_en"]

    def __init__(self, *args, **kwargs):
        super(QuizAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["questions"].initial = (
                self.instance.question_set.all().select_subclasses()
            )

    def save(self, commit=True):
        quiz = super(QuizAdminForm, self).save(commit=False)
        quiz.save()
        quiz.question_set.set(self.cleaned_data["questions"])
        self.save_m2m()
        return quiz


class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "school", "category", "exam_paper", "single_attempt")
    list_filter = ("course__school", "category", "exam_paper", "single_attempt")

    @admin.display(description="School")
    def school(self, obj):
        return obj.course.school

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(course__school=getattr(request.user, "school_id", None))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        school_id = getattr(request.user, "school_id", None)
        if db_field.name == "course" and not (request.user.is_superuser and not school_id):
            kwargs["queryset"] = db_field.remote_field.model.objects.filter(school_id=school_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    # form = QuizAdminForm
    # fields = (
    #     "title",
    #     "description",
    # )
    # list_display = ("title",)
    # # list_filter = ('category',)
    # search_fields = (
    #     "description",
    #     "category",
    # )


class MCQuestionAdmin(admin.ModelAdmin):
    list_display = ("content", "marks")
    # list_filter = ('category',)
    fieldsets = [
        ("figure" "quiz" "choice_order", {"fields": ("content", "marks", "explanation")})
    ]

    search_fields = ("content", "explanation")
    filter_horizontal = ("quiz",)

    inlines = [ChoiceInline]


class ProgressAdmin(admin.ModelAdmin):
    search_fields = (
        "user",
        "score",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(user__school=getattr(request.user, "school_id", None))


class EssayQuestionAdmin(admin.ModelAdmin):
    list_display = ("content", "marks")
    # list_filter = ('category',)
    fields = (
        "content",
        "marks",
        "quiz",
        "explanation",
    )
    search_fields = ("content", "explanation")
    filter_horizontal = ("quiz",)


admin.site.register(Quiz, QuizAdmin)
admin.site.register(MCQuestion, MCQuestionAdmin)
admin.site.register(Progress, ProgressAdmin)
admin.site.register(EssayQuestion, EssayQuestionAdmin)
admin.site.register(QuestionGrade)
admin.site.register(Sitting)
