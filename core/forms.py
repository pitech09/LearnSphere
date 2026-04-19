from django import forms

from course.models import Subject
from .models import NewsAndEvents, Session, Term

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        lecturers = User.objects.filter(is_lecturer=True)

        print(" LECTURERS IN SYSTEM:")
        for u in lecturers:
            print(u.id, u.username, u.is_lecturer)

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
class SessionForm(forms.ModelForm):
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
        model = Session
        fields = ["session", "is_current", "next_begins"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})