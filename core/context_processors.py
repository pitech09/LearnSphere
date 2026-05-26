from django.utils import timezone

from core.models import SCHOOL_STATUS_TRIAL


def school_trial(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    school = getattr(user, "school", None)
    if not school or school.status != SCHOOL_STATUS_TRIAL:
        return {}

    days_left = None
    if school.trial_ends_on:
        days_left = max((school.trial_ends_on - timezone.localdate()).days, 0)

    return {
        "trial_school": school,
        "trial_days_left": days_left,
    }
