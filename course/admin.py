from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Subject, SubjectAllocation, Upload, UploadVideo

class SubjectAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "school", "class_assigned", "teacher")
    list_filter = ("school", "class_assigned", "teacher")

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
        school_id = getattr(request.user, "school_id", None)
        if not (request.user.is_superuser and not school_id):
            if db_field.name == "school":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(pk=school_id)
            elif db_field.name == "class_assigned":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(school_id=school_id)
            elif db_field.name == "teacher":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(school_id=school_id, is_lecturer=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class UploadAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "school")

    @admin.display(description="School")
    def school(self, obj):
        return obj.subject.school

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(subject__school=getattr(request.user, "school_id", None))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        school_id = getattr(request.user, "school_id", None)
        if db_field.name == "subject" and not (request.user.is_superuser and not school_id):
            kwargs["queryset"] = Subject.objects.filter(school_id=school_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SubjectAllocationAdmin(admin.ModelAdmin):
    list_display = ("teacher", "school", "session")

    @admin.display(description="School")
    def school(self, obj):
        return obj.teacher.school

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(teacher__school=getattr(request.user, "school_id", None))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        school_id = getattr(request.user, "school_id", None)
        if not (request.user.is_superuser and not school_id):
            if db_field.name == "teacher":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(school_id=school_id, is_lecturer=True)
            elif db_field.name == "session":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(school_id=school_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

admin.site.register(Subject, SubjectAdmin)
admin.site.register(SubjectAllocation, SubjectAllocationAdmin)
admin.site.register(Upload, UploadAdmin)
admin.site.register(UploadVideo, UploadAdmin)
