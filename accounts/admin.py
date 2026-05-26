from django.contrib import admin
from .models import User, Student, Parent, TeacherProfile



class UserAdmin(admin.ModelAdmin):
    list_display = [
        "get_full_name",
        "username",
        "school",
        "email",
        "is_active",
        "is_student",
        "is_lecturer",
        "is_parent",
        "is_staff",
    ]
    list_filter = ["school", "is_student", "is_lecturer", "is_parent", "is_staff", "is_superuser"]
    search_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
        "is_active",
        "is_lecturer",
        "is_parent",
        "is_staff",
    ]

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
        if db_field.name == "school" and not (request.user.is_superuser and not getattr(request.user, "school_id", None)):
            kwargs["queryset"] = db_field.remote_field.model.objects.filter(pk=getattr(request.user, "school_id", None))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Meta:
        managed = True
        verbose_name = "User"
        verbose_name_plural = "Users"

admin.site.register(User, UserAdmin)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student", "school", "level", "student_class")
    list_filter = ("student__school", "level", "student_class")
    search_fields = (
        "student__username",
        "student__first_name",
        "student__last_name",
        "student_class__name",
    )

    @admin.display(description="School")
    def school(self, obj):
        return obj.student.school

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(student__school=getattr(request.user, "school_id", None))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        school_id = getattr(request.user, "school_id", None)
        if not (request.user.is_superuser and not school_id):
            if db_field.name == "student":
                kwargs["queryset"] = User.objects.filter(school_id=school_id, is_student=True)
            elif db_field.name == "student_class":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(school_id=school_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ParentAdmin(admin.ModelAdmin):
    list_display = ("user", "school", "student", "first_name", "last_name", "phone", "email", "relation_ship")
    list_filter = ("user__school", "relation_ship")
    search_fields = (
        "user__username",
        "first_name",
        "last_name",
        "phone",
        "email",
        "student__student__first_name",
        "student__student__last_name",
    )

    @admin.display(description="School")
    def school(self, obj):
        return obj.user.school

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(user__school=getattr(request.user, "school_id", None))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        school_id = getattr(request.user, "school_id", None)
        if not (request.user.is_superuser and not school_id):
            if db_field.name == "user":
                kwargs["queryset"] = User.objects.filter(school_id=school_id, is_parent=True)
            elif db_field.name == "student":
                kwargs["queryset"] = Student.objects.filter(student__school_id=school_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "school",
        "staff_number",
        "specialization",
        "qualification",
        "employment_date",
        "is_class_teacher",
    )
    list_filter = ("user__school", "is_class_teacher", "specialization")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "staff_number",
        "specialization",
    )

    @admin.display(description="School")
    def school(self, obj):
        return obj.user.school

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(user__school=getattr(request.user, "school_id", None))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        school_id = getattr(request.user, "school_id", None)
        if db_field.name == "user" and not (request.user.is_superuser and not school_id):
            kwargs["queryset"] = User.objects.filter(school_id=school_id, is_lecturer=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Student, StudentAdmin)
admin.site.register(Parent, ParentAdmin)
admin.site.register(TeacherProfile, TeacherProfileAdmin)
