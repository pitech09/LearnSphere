from django import forms

from course.models import Subject
from .models import NewsAndEvents, School, Session, Term

from django import forms
from .models import SchoolClass
from accounts.models import User


class SchoolClassForm(forms.ModelForm):
    class_teacher = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=True,
        label="Class Teacher"
    )
    LEVELS = [
        ("F1", "Grade 8"),
        ("F2", "Grade 9"),
        ("F3", "Grade 10"),
        ("F4", "Grade 11"),
        ("F5", "Grade 12"),
    ]

    level = forms.ChoiceField(choices=LEVELS)

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)

        lecturers = User.objects.filter(is_lecturer=True)
        if school:
            lecturers = lecturers.filter(school=school)

        self.fields['class_teacher'].queryset = lecturers

        # optional styling consistency
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control"
            })

    class Meta:
        model = SchoolClass
        fields = ['name', 'level', 'class_teacher']



# =========================================================
# 📢 NEWS & EVENTS FORM
# =========================================================
class NewsAndEventsForm(forms.ModelForm):
    class Meta:
        model = NewsAndEvents
        fields = ("title", "summary", "posted_as")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


# =========================================================
# 📅 SESSION FORM
# =========================================================
from django.core.exceptions import ValidationError
from .models import Session

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['session', 'is_current', 'next_session_begins']

    def clean(self):
        cleaned_data = super().clean()
        session_name = cleaned_data.get('session')
        school = getattr(self, 'school', None)  # You'll need to pass school to the form
        if school and session_name:
            if Session.objects.filter(school=school, session=session_name).exists():
                raise ValidationError("A session with this name already exists for your school.")
        return cleaned_data

# =========================================================
# 📆 TERM FORM (UPDATED - replaces SemesterForm)
# =========================================================
class TermForm(forms.ModelForm):

    name = forms.ChoiceField(
        choices=Term._meta.get_field("name").choices,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    is_current = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput()
    )

    next_begins = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control"
            }
        ),
        required=False
    )

    class Meta:
        model = Term
        fields = ["session", "name", "is_current", "next_begins"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["session"].widget.attrs.update({
            "class": "form-control"
        })

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['title', 'code', 'summary', 'class_assigned', 'teacher']

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields["class_assigned"].queryset = self.fields["class_assigned"].queryset.filter(school=school)
            self.fields["teacher"].queryset = self.fields["teacher"].queryset.filter(school=school)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


class CurrentQuarterForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ["current_quarter"]
        widgets = {
            "current_quarter": forms.Select(attrs={"class": "form-control"}),
        }


class SchoolPlatformForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            "status",
            "plan",
            "subscription_amount",
            "max_students",
            "is_unlimited",
            "last_payment_on",
            "next_payment_due_on",
            "suspended_reason",
            "is_active",
        ]
        widgets = {
            "last_payment_on": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "next_payment_due_on": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "suspended_reason": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        # Make auto-calculated fields read-only in the UI
        self.fields["subscription_amount"].widget.attrs["readonly"] = True
        self.fields["max_students"].widget.attrs["readonly"] = True
        self.fields["is_unlimited"].widget.attrs["disabled"] = True
