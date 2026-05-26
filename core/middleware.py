from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from core.models import SCHOOL_STATUS_SUSPENDED, SCHOOL_STATUS_TRIAL


class SchoolSuspensionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            school = getattr(user, "school", None)
            if school and self._trial_has_expired(school):
                school.status = SCHOOL_STATUS_SUSPENDED
                school.is_active = False
                school.suspended_reason = "The 7 day free trial has expired. Please upgrade to continue using LearnSphere."
                school.save(update_fields=["status", "is_active", "suspended_reason", "updated_at"])
            if school and school.is_suspended and not self._is_allowed_path(request):
                return render(request, "core/school_suspended.html", {"school": school}, status=403)
        return self.get_response(request)

    def _is_allowed_path(self, request):
        allowed_paths = {
            reverse("logout"),
        }
        return (
            request.path in allowed_paths
            or request.path.startswith("/static/")
            or request.path.startswith("/media/")
        )

    def _trial_has_expired(self, school):
        return (
            school.status == SCHOOL_STATUS_TRIAL
            and school.trial_ends_on
            and school.trial_ends_on < timezone.localdate()
        )
