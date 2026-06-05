from django.contrib import admin
from .models import (
    ActivityLog,
    AttendanceRecord,
    Exam,
    ExamSchedule,
    FeePayment,
    Expense,
    Income,
    MarkEntry,
    NewsAndEvents,
    School,
    SchoolClass,
    SchoolFee,
    Session,
    Term,
    TimetableEntry,
)


class TenantScopedAdminMixin:
    tenant_field = "school"

    def is_platform_admin(self, request):
        return request.user.is_superuser and not getattr(request.user, "school_id", None)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_platform_admin(request):
            return qs
        school_id = getattr(request.user, "school_id", None)
        if not school_id:
            return qs.none()
        return qs.filter(**{self.tenant_field: school_id})

    def save_model(self, request, obj, form, change):
        if hasattr(obj, self.tenant_field) and not getattr(obj, f"{self.tenant_field}_id", None):
            obj.school = getattr(request.user, "school", None)
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        school_id = getattr(request.user, "school_id", None)
        if not self.is_platform_admin(request) and school_id:
            if db_field.name == "school":
                kwargs["queryset"] = School.objects.filter(pk=school_id)
            elif db_field.name in {"student"}:
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(student__school_id=school_id)
            elif db_field.name in {"school_class", "class_assigned"}:
                kwargs["queryset"] = SchoolClass.objects.filter(school_id=school_id)
            elif db_field.name in {"subject"}:
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(school_id=school_id)
            elif db_field.name in {"teacher", "class_teacher", "invigilator", "recorded_by", "processed_by", "received_by"}:
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(school_id=school_id)
            elif db_field.name in {"session"}:
                kwargs["queryset"] = Session.objects.filter(school_id=school_id)
            elif db_field.name in {"term"}:
                kwargs["queryset"] = Term.objects.filter(school_id=school_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "subdomain",
        "status",
        "plan",
        "current_quarter",
        "subscription_amount",
        "last_payment_on",
        "next_payment_due_on",
        "is_active",
        "created_at",
    )
    list_filter = ("status", "plan", "is_active")
    search_fields = ("name", "subdomain", "email", "phone")
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(pk=getattr(request.user, "school_id", None))


class NewsAndEventsAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ("title", "posted_as", "created_at", "updated_at")
    list_filter = ("posted_as", "created_at")
    search_fields = ("title", "summary")


class SchoolClassAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "school", "level", "class_teacher", "is_active")
    list_filter = ("school", "level", "is_active")
    search_fields = ("name", "class_teacher__first_name", "class_teacher__last_name")


class SessionAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ("session", "school", "is_current", "next_session_begins")
    list_filter = ("school", "is_current")
    search_fields = ("session", "school__name")


class TermAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "school", "session", "is_current", "next_begins")
    list_filter = ("school", "session", "is_current")


class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0


class SchoolFeeAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = (
        "student",
        "school",
        "description",
        "session",
        "term",
        "amount_due",
        "discount",
        "total_paid_display",
        "balance_display",
        "due_date",
        "status",
    )
    list_filter = ("school", "status", "session", "term", "due_date")
    search_fields = (
        "student__student__username",
        "student__student__first_name",
        "student__student__last_name",
        "description",
    )
    inlines = [FeePaymentInline]

    @admin.display(description="Paid")
    def total_paid_display(self, obj):
        return obj.total_paid

    @admin.display(description="Balance")
    def balance_display(self, obj):
        return obj.balance


class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ("fee", "amount", "paid_on", "method", "reference", "received_by")
    list_filter = ("method", "paid_on")
    search_fields = ("reference", "fee__student__student__first_name", "fee__student__student__last_name")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(fee__school=getattr(request.user, "school_id", None))


class AttendanceRecordAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ("date", "student", "school", "school_class", "subject", "status", "recorded_by")
    list_filter = ("school", "status", "date", "school_class", "subject")
    search_fields = ("student__student__first_name", "student__student__last_name", "remarks")


class ExpenseAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ("title", "school", "category", "amount", "expense_date", "recorded_by")
    list_filter = ("school", "category", "expense_date")
    search_fields = ("title", "description", "receipt_number")


class IncomeAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ("source", "school", "category", "amount", "income_date", "recorded_by")
    list_filter = ("school", "category", "income_date")
    search_fields = ("source", "reference", "notes")


class ExamScheduleInline(admin.TabularInline):
    model = ExamSchedule
    extra = 1


class ExamAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "school", "school_class", "session", "term", "starts_on", "ends_on", "status", "results_published")
    list_filter = ("school", "status", "results_published", "session", "term", "school_class")
    search_fields = ("name", "school_class__name")
    inlines = [ExamScheduleInline]


class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ("exam", "subject", "date", "start_time", "end_time", "venue", "invigilator")
    list_filter = ("date", "exam", "subject")
    search_fields = ("exam__name", "subject__title", "venue")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser and not getattr(request.user, "school_id", None):
            return qs
        return qs.filter(exam__school=getattr(request.user, "school_id", None))


class MarkEntryAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = (
        "student",
        "school",
        "subject",
        "exam",
        "continuous_assessment",
        "exam_mark",
        "final_mark",
        "status",
        "processed_by",
    )
    list_filter = ("school", "status", "subject", "exam")
    search_fields = ("student__student__first_name", "student__student__last_name", "subject__title")
    readonly_fields = ("final_mark", "processed_at")


class TimetableEntryAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ("school_class", "school", "day", "start_time", "end_time", "subject", "teacher", "room", "is_active")
    list_filter = ("school", "day", "school_class", "teacher", "is_active")
    search_fields = ("school_class__name", "subject__title", "teacher__first_name", "teacher__last_name", "room")


class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("message", "created_at")
    search_fields = ("message",)
    readonly_fields = ("message", "created_at")

admin.site.register(SchoolClass, SchoolClassAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Term, TermAdmin)
admin.site.register(NewsAndEvents, NewsAndEventsAdmin)
admin.site.register(SchoolFee, SchoolFeeAdmin)
admin.site.register(FeePayment, FeePaymentAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Income, IncomeAdmin)
admin.site.register(AttendanceRecord, AttendanceRecordAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(ExamSchedule, ExamScheduleAdmin)
admin.site.register(MarkEntry, MarkEntryAdmin)
admin.site.register(TimetableEntry, TimetableEntryAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)
