from django import forms

from course.models import Subject
from .models import NewsAndEvents, School, Session, Term, Exam, ExamSchedule
from .models import SchoolClass
from accounts.models import User, Student
from .models import SchoolFee, FeePayment
from django.forms import inlineformset_factory
from .models import TimetableEntry

from .models import MarkEntry

class MarkEntryByLevelForm(forms.Form):
    level = forms.ChoiceField(choices=SchoolClass.LEVEL_CHOICES, label="Level")
    subject = forms.ModelChoiceField(queryset=Subject.objects.none(), label="Subject")
    exam = forms.ModelChoiceField(queryset=Exam.objects.none(), label="Exam", required=False)

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['subject'].queryset = Subject.objects.filter(school=school)
            self.fields['exam'].queryset = Exam.objects.filter(school=school)

class MarkEntryByLevelForm(forms.Form):
    level = forms.ChoiceField(choices=SchoolClass.LEVEL_CHOICES, label="Level")
    subject = forms.ModelChoiceField(queryset=Subject.objects.none(), label="Subject")
    exam = forms.ModelChoiceField(queryset=Exam.objects.none(), label="Exam", required=False)
    continuous_assessment = forms.DecimalField(max_digits=5, decimal_places=2, required=False, label="Continuous Assessment (0-100)")
    exam_mark = forms.DecimalField(max_digits=5, decimal_places=2, required=False, label="Exam Mark (0-100)")

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['subject'].queryset = Subject.objects.filter(school=school)
            self.fields['exam'].queryset = Exam.objects.filter(school=school)


class TimetableEntryForm(forms.ModelForm):
    class Meta:
        model = TimetableEntry
        fields = ['school_class', 'subject', 'teacher', 'day', 'start_time', 'end_time', 'room', 'is_active']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)
            self.fields['subject'].queryset = Subject.objects.filter(school=school)
            self.fields['teacher'].queryset = User.objects.filter(school=school, is_lecturer=True)

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'session', 'term', 'school_class', 'starts_on', 'ends_on', 'status']
        widgets = {
            'starts_on': forms.DateInput(attrs={'type': 'date'}),
            'ends_on': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)
            self.fields['session'].queryset = Session.objects.filter(school=school)
            self.fields['term'].queryset = Term.objects.filter(school=school)

class ExamScheduleForm(forms.ModelForm):
    class Meta:
        model = ExamSchedule
        fields = ['subject', 'date', 'start_time', 'end_time', 'venue', 'invigilator']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['subject'].queryset = Subject.objects.filter(school=school)
            self.fields['invigilator'].queryset = User.objects.filter(school=school, is_lecturer=True)

ExamScheduleFormSet = inlineformset_factory(
    Exam, ExamSchedule, form=ExamScheduleForm, extra=1, can_delete=True
)

class SchoolFeeForm(forms.ModelForm):
    class Meta:
        model = SchoolFee
        fields = ['student', 'session', 'term', 'description', 'amount_due', 'discount', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            # Limit student choices to those in the school
            self.fields['student'].queryset = Student.objects.filter(student__school=school)
            self.fields['session'].queryset = Session.objects.filter(school=school)
            self.fields['term'].queryset = Term.objects.filter(school=school)

class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = ['amount', 'paid_on', 'method', 'reference', 'notes']
        widgets = {
            'paid_on': forms.DateInput(attrs={'type': 'date'}),
        }


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



class BulkFeeForm(forms.Form):
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.none(), label="Class")
    session = forms.ModelChoiceField(queryset=Session.objects.none(), label="Session")
    term = forms.ModelChoiceField(queryset=Term.objects.none(), label="Term", required=False)
    description = forms.CharField(max_length=160, initial="Tuition fees")
    amount_due = forms.DecimalField(max_digits=10, decimal_places=2)
    discount = forms.DecimalField(max_digits=10, decimal_places=2, required=False, initial=0)
    due_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)
            self.fields['session'].queryset = Session.objects.filter(school=school)
            self.fields['term'].queryset = Term.objects.filter(school=school)

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
