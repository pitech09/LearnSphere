from django import forms

from accounts.models import User, Student
from core.models import SchoolClass
from .models import Subject, Upload, UploadVideo

class AssignClassForm(forms.ModelForm):
    
    class Meta:
        model = Student
        fields = ["student_class"]
        widgets = {
            "student_class": forms.Select(attrs={"class": "form-control"})
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        classes = SchoolClass.objects.filter(is_active=True)
        if school:
            classes = classes.filter(school=school)
        self.fields["student_class"].queryset = classes.select_related("class_teacher")


class SubjectAddForm(forms.ModelForm):


    class_assigned = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all(),
        required=True,
        label="Classes"
    )

    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(is_lecturer=True),
        required=True,
        label="Teacher"
    )
    
    is_electable = forms.BooleanField(
        required=False,
        label="Electable Subject",
        help_text="Check if students can optionally add this subject",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = Subject
        fields = ["title", "code", "summary", "class_assigned", "teacher", "is_electable"]

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields["class_assigned"].queryset = SchoolClass.objects.filter(school=school)
            self.fields["teacher"].queryset = User.objects.filter(is_lecturer=True, school=school)

        # KEEP ONLY UI styling here
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control"
            })
# =========================================================
# FILE UPLOAD FORM
# =========================================================
class UploadFormFile(forms.ModelForm):
    class Meta:
        model = Upload
        fields = ("title", "file")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["file"].widget.attrs.update({"class": "form-control"})


# =========================================================
# VIDEO UPLOAD FORM
# =========================================================
class UploadFormVideo(forms.ModelForm):
    class Meta:
        model = UploadVideo
        fields = ("title", "video")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["video"].widget.attrs.update({"class": "form-control"})
