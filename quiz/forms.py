from django import forms
from django.forms.widgets import RadioSelect, Textarea
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _
from django.forms.models import inlineformset_factory
from .models import EssayQuestion, Question, Quiz, MCQuestion, Choice


QUESTION_TYPE_MCQ = "mcq"
QUESTION_TYPE_ESSAY = "essay"
QUESTION_TYPE_CHOICES = (
    (QUESTION_TYPE_MCQ, _("Multiple choice")),
    (QUESTION_TYPE_ESSAY, _("Short answers / Essay")),
)


class QuestionForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        choice_list = [x for x in question.get_choices_list()]
        self.fields["answers"] = forms.ChoiceField(
            choices=choice_list,
            widget=RadioSelect,
            label=_("Choose one answer"),
        )


class EssayForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(EssayForm, self).__init__(*args, **kwargs)
        self.fields["answers"] = forms.CharField(
            label=_("Your answer"),
            widget=Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": _("Type your short answer or essay response here."),
                }
            ),
        )


class QuizAddForm(forms.ModelForm):
    question_type = forms.ChoiceField(
        choices=QUESTION_TYPE_CHOICES,
        initial=QUESTION_TYPE_MCQ,
        required=False,
        label=_("Question type"),
        help_text=_("Choose the first question type to add after saving this assessment."),
    )

    class Meta:
        model = Quiz
        exclude = []

    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label=_("Questions"),
        widget=FilteredSelectMultiple(verbose_name=_("Questions"), is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        super(QuizAddForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["questions"].initial = (
                self.instance.question_set.all().select_subclasses()
            )
            self.fields.pop("question_type", None)

    def save(self, commit=True):
        quiz = super(QuizAddForm, self).save(commit=False)
        quiz.save()
        quiz.question_set.set(self.cleaned_data["questions"])
        self.save_m2m()
        return quiz


class PhysicalTestForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["title", "test_date", "description"]
        widgets = {
            "test_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class MCQuestionForm(forms.ModelForm):
    class Meta:
        model = MCQuestion
        exclude = ()


class EssayQuestionForm(forms.ModelForm):
    class Meta:
        model = EssayQuestion
        exclude = ()


class MCQuestionFormSet(forms.BaseInlineFormSet):
    def clean(self):
        """
        Custom validation for the formset to ensure:
        1. At least two choices are provided and not marked for deletion.
        2. At least one of the choices is marked as correct.
        """
        super().clean()

        # Collect non-deleted forms
        valid_forms = [
            form for form in self.forms if not form.cleaned_data.get("DELETE", True)
        ]

        valid_choices = [
            "choice_text" in form.cleaned_data.keys() for form in valid_forms
        ]
        if not all(valid_choices):
            raise forms.ValidationError("You must add a valid choice name.")

        # If all forms are deleted, raise a validation error
        if len(valid_forms) < 2:
            raise forms.ValidationError("You must provide at least two choices.")

        # Check if at least one of the valid forms is marked as correct
        correct_choices = [
            form.cleaned_data.get("correct", False) for form in valid_forms
        ]

        if not any(correct_choices):
            raise forms.ValidationError("One choice must be marked as correct.")

        if correct_choices.count(True) > 1:
            raise forms.ValidationError("Only one choice must be marked as correct.")


MCQuestionFormSet = inlineformset_factory(
    MCQuestion,
    Choice,
    form=MCQuestionForm,
    formset=MCQuestionFormSet,
    fields=["choice_text", "correct"],
    can_delete=True,
    extra=5,
)
