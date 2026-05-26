from .utils import (
    generate_student_credentials,
    generate_lecturer_credentials,
    send_new_account_sms,
)

from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Student
from core.datastore.loaders import SchoolDataLoader


@receiver(post_save, sender=Student)
def refresh_student_cache(sender, instance, **kwargs):

    SchoolDataLoader.refresh_student(instance)
    
def post_save_account_receiver(instance=None, created=False, *args, **kwargs):
    """
    Send SMS notification for accounts that need generated credentials.
    """
    if created and not instance.has_usable_password():
        if instance.is_student:
            username, password = generate_student_credentials()
            instance.username = username
            instance.set_password(password)
            instance.save()
            send_new_account_sms(instance, password)

        if instance.is_lecturer:
            username, password = generate_lecturer_credentials()
            instance.username = username
            instance.set_password(password)
            instance.save()
            send_new_account_sms(instance, password)
