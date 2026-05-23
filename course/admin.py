from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Subject, SubjectAllocation, Upload


class SchoolScopedAdminMixin:
    def is_platform_admin(self, request):
        return request.user.is_superuser and not getattr(request.user, "school_id", None)


class SubjectAdmin(SchoolScopedAdminMixin, admin.ModelAdmin):
    list_display = ("title", "code", "school", "class_assigned", "teacher")
    list_filter = ("school", "class_assigned", "teacher")
    search_fields = ("title", "code", "class_assigned__name", "teacher__first_name", "teacher__last_name")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_platform_admin(request):
            return qs
        return qs.filter(school=getattr(request.user, "school_id", None))

    def save_model(self, request, obj, form, change):
        if not obj.school_id:
            obj.school = getattr(request.user, "school", None)
        super().save_model(request, obj, form, change)


class SubjectAllocationAdmin(SchoolScopedAdminMixin, admin.ModelAdmin):
    list_display = ("teacher", "session")
    list_filter = ("session",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_platform_admin(request):
            return qs
        return qs.filter(teacher__school=getattr(request.user, "school_id", None))


class UploadAdmin(SchoolScopedAdminMixin, admin.ModelAdmin):
    list_display = ("title", "subject", "updated_date", "upload_time")
    list_filter = ("subject", "updated_date")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_platform_admin(request):
            return qs
        return qs.filter(subject__school=getattr(request.user, "school_id", None))
    

admin.site.register(Subject, SubjectAdmin)
admin.site.register(SubjectAllocation, SubjectAllocationAdmin)
admin.site.register(Upload, UploadAdmin)
