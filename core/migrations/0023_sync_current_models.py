# Generated manually to sync core models with the current codebase.

from django.conf import settings
from django.db import migrations, models
from django.db.models import deletion
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_newsandevents_target_audience_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Expense",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("category", models.CharField(choices=[("salaries", "Salaries & Wages"), ("utilities", "Utilities (Water, Electricity, Internet)"), ("maintenance", "Maintenance & Repairs"), ("supplies", "School Supplies & Equipment"), ("transport", "Transportation"), ("food", "Food & Catering"), ("events", "Events & Activities"), ("marketing", "Marketing & Advertising"), ("insurance", "Insurance"), ("rent", "Rent & Leasing"), ("technology", "Technology & Software"), ("professional", "Professional Services (Legal, Audit)"), ("other", "Other Expenses")], default="other", max_length=30)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("description", models.TextField(blank=True)),
                ("expense_date", models.DateField(default=timezone.localdate)),
                ("receipt_number", models.CharField(blank=True, help_text="Optional receipt or invoice reference", max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("recorded_by", models.ForeignKey(blank=True, null=True, on_delete=deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("school", models.ForeignKey(on_delete=deletion.CASCADE, related_name="expenses", to="core.school")),
            ],
            options={
                "ordering": ("-expense_date", "-created_at"),
            },
        ),
        migrations.AddField(
            model_name="school",
            name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="profile_pictures/"),
        ),
        migrations.AddField(
            model_name="school",
            name="website",
            field=models.URLField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name="school",
            name="registration_number",
        ),
        migrations.RemoveField(
            model_name="school",
            name="trial_ends_on",
        ),
        migrations.AddField(
            model_name="exam",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="exam",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="markentry",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="markentry",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="timetableentry",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="timetableentry",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="attendancerecord",
            options={},
        ),
        migrations.AlterModelOptions(
            name="exam",
            options={},
        ),
        migrations.AlterModelOptions(
            name="examschedule",
            options={},
        ),
        migrations.AlterModelOptions(
            name="markentry",
            options={},
        ),
        migrations.AlterModelOptions(
            name="school",
            options={},
        ),
        migrations.AlterModelOptions(
            name="timetableentry",
            options={"ordering": ("day", "start_time")},
        ),
        migrations.AlterField(
            model_name="attendancerecord",
            name="recorded_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name="attendancerecord",
            name="remarks",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="attendancerecord",
            name="school_class",
            field=models.ForeignKey(blank=True, null=True, on_delete=deletion.CASCADE, to="core.schoolclass"),
        ),
        migrations.AlterField(
            model_name="attendancerecord",
            name="status",
            field=models.CharField(choices=[("present", "Present"), ("absent", "Absent"), ("late", "Late"), ("excused", "Excused")], max_length=10),
        ),
        migrations.AlterField(
            model_name="attendancerecord",
            name="student",
            field=models.ForeignKey(on_delete=deletion.CASCADE, to="accounts.student"),
        ),
        migrations.AlterField(
            model_name="school",
            name="address",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="school",
            name="current_quarter",
            field=models.CharField(choices=[("Q1", "Quarter 1"), ("Q2", "Quarter 2"), ("Q3", "Quarter 3"), ("Q4", "Quarter 4")], default="Q1", max_length=4),
        ),
        migrations.AlterField(
            model_name="school",
            name="is_unlimited",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="school",
            name="max_students",
            field=models.IntegerField(default=100),
        ),
        migrations.AlterField(
            model_name="school",
            name="name",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="school",
            name="phone",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="school",
            name="slug",
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="school",
            name="subdomain",
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="school",
            name="subscription_amount",
            field=models.DecimalField(decimal_places=2, default=250, max_digits=10),
        ),
        migrations.AlterField(
            model_name="exam",
            name="ends_on",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="exam",
            name="name",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="exam",
            name="school_class",
            field=models.ForeignKey(blank=True, null=True, on_delete=deletion.CASCADE, related_name="exams", to="core.schoolclass"),
        ),
        migrations.AlterField(
            model_name="exam",
            name="starts_on",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="markentry",
            name="continuous_assessment",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name="markentry",
            name="exam",
            field=models.ForeignKey(blank=True, null=True, on_delete=deletion.SET_NULL, to="core.exam"),
        ),
        migrations.AlterField(
            model_name="markentry",
            name="exam_mark",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name="markentry",
            name="status",
            field=models.CharField(default="draft", max_length=20),
        ),
        migrations.AlterField(
            model_name="markentry",
            name="student",
            field=models.ForeignKey(on_delete=deletion.CASCADE, to="accounts.student"),
        ),
        migrations.AlterField(
            model_name="markentry",
            name="subject",
            field=models.ForeignKey(on_delete=deletion.CASCADE, to="course.subject"),
        ),
        migrations.AlterField(
            model_name="school",
            name="website",
            field=models.URLField(blank=True),
        ),
        migrations.AlterField(
            model_name="timetableentry",
            name="day",
            field=models.CharField(choices=[("monday", "Monday"), ("tuesday", "Tuesday"), ("wednesday", "Wednesday"), ("thursday", "Thursday"), ("friday", "Friday"), ("saturday", "Saturday"), ("sunday", "Sunday")], max_length=10),
        ),
        migrations.AlterField(
            model_name="timetableentry",
            name="room",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddIndex(
            model_name="attendancerecord",
            index=models.Index(fields=["school", "date"], name="attendance_school_date_idx"),
        ),
        migrations.AddIndex(
            model_name="attendancerecord",
            index=models.Index(fields=["school", "student", "date"], name="attendance_student_date_idx"),
        ),
        migrations.AddIndex(
            model_name="exam",
            index=models.Index(fields=["school", "status"], name="exam_school_status_idx"),
        ),
        migrations.AddIndex(
            model_name="exam",
            index=models.Index(fields=["school", "starts_on"], name="exam_school_starts_idx"),
        ),
        migrations.AddIndex(
            model_name="examschedule",
            index=models.Index(fields=["exam", "date"], name="schedule_exam_date_idx"),
        ),
        migrations.AddIndex(
            model_name="expense",
            index=models.Index(fields=["school", "-expense_date"], name="expense_school_date_idx"),
        ),
        migrations.AddIndex(
            model_name="expense",
            index=models.Index(fields=["school", "category"], name="expense_school_category_idx"),
        ),
        migrations.RemoveIndex(
            model_name="attendancerecord",
            name="att_school_date_status_idx",
        ),
        migrations.RemoveIndex(
            model_name="attendancerecord",
            name="att_school_class_date_idx",
        ),
        migrations.RemoveIndex(
            model_name="exam",
            name="exam_school_start_idx",
        ),
        migrations.RemoveIndex(
            model_name="markentry",
            name="mark_school_status_idx",
        ),
        migrations.RemoveIndex(
            model_name="markentry",
            name="mark_school_student_idx",
        ),
        migrations.RemoveIndex(
            model_name="school",
            name="school_status_active_idx",
        ),
        migrations.RemoveIndex(
            model_name="school",
            name="school_next_due_idx",
        ),
        migrations.RenameIndex(
            model_name="timetableentry",
            new_name="tt_school_class_day_idx",
            old_name="time_school_class_day_idx",
        ),
        migrations.RenameIndex(
            model_name="timetableentry",
            new_name="tt_school_teacher_day_idx",
            old_name="time_school_teacher_idx",
        ),
        migrations.AlterUniqueTogether(
            name="examschedule",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="markentry",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="timetableentry",
            unique_together=set(),
        ),
    ]
