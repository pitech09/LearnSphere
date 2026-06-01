from django import forms
from django.utils import timezone

from course.models import Subject
from .models import PhysicalAssessment, PhysicalAssessmentMark


class PhysicalAssessmentForm(forms.ModelForm):
    """
    Form for creating and editing physical assessments (tests/assignments).
    """
    class Meta:
        model = PhysicalAssessment
        fields = ['subject', 'title', 'assessment_type', 'description', 'max_marks', 'date_conducted']
        widgets = {
            'date_conducted': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }

    def __init__(self, *args, school=None, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            # Filter subjects to only those taught by the teacher at the school
            if teacher:
                from django.db.models import Q
                self.fields['subject'].queryset = Subject.objects.filter(
                    Q(allocated_subjects__teacher=teacher) | Q(teacher=teacher),
                    school=school,
                ).distinct()
            else:
                self.fields['subject'].queryset = Subject.objects.filter(school=school)
        
        # Add form-control class to all fields
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

        # Set default date to today
        if not self.initial.get('date_conducted'):
            self.initial['date_conducted'] = timezone.localdate()


class PhysicalAssessmentMarkEntryForm(forms.Form):
    """
    Form for entering marks for multiple students for a physical assessment.
    """
    def __init__(self, *args, students=None, assessment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.students = students or []
        self.assessment = assessment
        
        if students:
            for student in students:
                # Get existing mark if any
                existing_mark = None
                if assessment:
                    try:
                        existing_mark = PhysicalAssessmentMark.objects.get(
                            assessment=assessment,
                            student=student
                        )
                    except PhysicalAssessmentMark.DoesNotExist:
                        pass
                
                # Create fields for each student
                self.fields[f'mark_{student.id}'] = forms.DecimalField(
                    label=f"{student.student.get_full_name()} ({student.student.username})",
                    max_digits=5,
                    decimal_places=2,
                    required=False,
                    min_value=0,
                    max_value=assessment.max_marks if assessment else 100,
                    initial=existing_mark.marks_obtained if existing_mark else None,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'min': '0',
                        'max': str(assessment.max_marks if assessment else 100),
                        'step': '0.01',
                    })
                )
                self.fields[f'remarks_{student.id}'] = forms.CharField(
                    label="Remarks",
                    required=False,
                    max_length=200,
                    initial=existing_mark.remarks if existing_mark else '',
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'Optional remarks',
                    })
                )