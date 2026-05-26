import threading
import string
import json
import logging
import urllib.request
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

logger = logging.getLogger(__name__)


def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return get_random_string(length, chars)

def generate_student_id():
    # Generate a username based on first and last name and registration date
    registered_year = datetime.now().strftime("%Y")
    students_count = get_user_model().objects.filter(is_student=True).count()
    return f"{settings.STUDENT_ID_PREFIX}-{registered_year}-{students_count}"


def generate_lecturer_id():
    # Generate a username based on first and last name and registration date
    registered_year = datetime.now().strftime("%Y")
    lecturers_count = get_user_model().objects.filter(is_lecturer=True).count()
    return f"{settings.LECTURER_ID_PREFIX}-{registered_year}-{lecturers_count}"


def generate_student_credentials():
    return generate_student_id(), generate_password()


def generate_lecturer_credentials():
    return generate_lecturer_id(), generate_password()


class SMSThread(threading.Thread):
    def __init__(self, phone_number, message):
        self.phone_number = phone_number
        self.message = message
        threading.Thread.__init__(self)

    def run(self):
        send_sms(self.phone_number, self.message)


def send_sms(phone_number, message):
    api_key = getattr(settings, "TEXTBEE_API_KEY", "")
    device_id = getattr(settings, "TEXTBEE_DEVICE_ID", "")
    base_url = getattr(settings, "TEXTBEE_BASE_URL", "https://api.textbee.dev")

    if not phone_number:
        logger.warning("SMS skipped because no phone number was supplied.")
        return None

    if not api_key or not device_id:
        logger.info("[SMS DRY RUN] To %s: %s", phone_number, message)
        return None

    url = f"{base_url.rstrip('/')}/api/v1/gateway/devices/{device_id}/send-sms"
    payload = json.dumps({
        "recipients": [phone_number],
        "message": message,
    }).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status
    except Exception:
        logger.exception("SMS send failed for %s", phone_number)
        return None


def build_account_credentials_message(user, password):
    school_name = user.school.name if getattr(user, "school", None) else "LearnSphere"
    role = "student" if user.is_student else "teacher"
    return (
        f"{school_name} {role} account created. "
        f"Username: {user.username}. Password: {password}. "
        "Please sign in and change your password."
    )


def send_new_account_sms(user, password):
    message = build_account_credentials_message(user, password)
    logger.info("[ACCOUNT CREATED] %s | %s", user.username, user.phone)
    SMSThread(user.phone, message).start()
