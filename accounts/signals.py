from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Student, User
from core.datastore.loaders import SchoolDataLoader

from .utils import (
    generate_student_credentials,
    generate_lecturer_credentials,
    send_new_account_sms,
)


# =========================================================
# STUDENT CACHE REFRESH
# =========================================================

@receiver(post_save, sender=Student)
def refresh_student_cache(sender, instance, **kwargs):

    if hasattr(SchoolDataLoader, "refresh_student"):
        SchoolDataLoader.refresh_student(instance)


# =========================================================
# USER ACCOUNT SETUP
# =========================================================

@receiver(post_save, sender=User)
def post_save_account_receiver(
    sender,
    instance,
    created,
    **kwargs
):
    """
    Auto-generate credentials for accounts
    missing usable passwords.
    """

    if not created:
        return

    if instance.has_usable_password():
        return

    password = None
    username = instance.username

    # =====================================================
    # STUDENT ACCOUNT
    # =====================================================

    if instance.is_student:

        username, password = (
            generate_student_credentials()
        )

    # =====================================================
    # LECTURER ACCOUNT
    # =====================================================

    elif instance.is_lecturer:

        username, password = (
            generate_lecturer_credentials()
        )

    # =====================================================
    # UPDATE USER SAFELY
    # =====================================================

    if password:

        User.objects.filter(
            pk=instance.pk
        ).update(
            username=username,
            password=User.objects.make_random_password()
        )

        instance.username = username
        instance.set_password(password)

        User.objects.filter(
            pk=instance.pk
        ).update(
            username=instance.username,
            password=instance.password,
        )

        send_new_account_sms(
            instance,
            password,
        )