import threading
import string
import json
import logging
import time
import urllib.request
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
import requests

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


def build_account_credentials_message(user, password):
    school_name = user.school.name if getattr(user, "school", None) else "LearnSphere"
    role = "student" if user.is_student else "teacher"
    # Minimised SMS: credentials only, no punctuation waste
    return (
        f"{school_name} {role}: "
        f"u:{user.username} p:{password} "
        f"{'https://learnsphere.onrender.com' if role == 'student' else 'https://learnsphere.onrender.com'}"
    )

def send_new_account_sms(user, password):
    """Send SMS via TextBee with retries and longer timeout."""
    message = build_account_credentials_message(user, password)

    textbee_api_key = getattr(settings, "TEXTBEE_API_KEY", None)
    textbee_device_id = getattr(settings, "TEXTBEE_DEVICE_ID", None)
    BASE_URL = 'https://api.textbee.dev/api/v1'   
    textbee_sim_subscription_id = getattr(settings, "TEXTBEE_SIM_SUBSCRIPTION_ID", None)

    if not textbee_api_key:
        return False, "Missing TEXTBEE_API_KEY"
    if not textbee_device_id:
        return False, "Missing TEXTBEE_DEVICE_ID"
    if not user.phone:
        return False, "Missing SMS recipient"
    
    print(f"Attempting to send SMS to {user.phone} via TextBee. Message: {message}")

    url = f"{BASE_URL}/gateway/devices/{textbee_device_id}/send-sms"
    payload = {
        "recipients": [str(user.phone)],
        "message": message,
    }
    if textbee_sim_subscription_id:
        try:
            payload["simSubscriptionId"] = int(textbee_sim_subscription_id)
        except (TypeError, ValueError):
            return False, "TEXTBEE_SIM_SUBSCRIPTION_ID must be a number"

    max_retries = 3
    timeout = 30  # seconds, increased from 20

    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": textbee_api_key,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError:
                data = {"response": response.text}
            message_id = data.get("id") or data.get("messageId") or data.get("batchId") or str(data)
            logger.info(f"SMS sent successfully to {user.phone} via TextBee. Result: {message_id}")
            return True, message_id

        except requests.Timeout:
            if attempt == max_retries - 1:
                logger.error(f"SMS timeout after {max_retries} attempts to {user.phone}")
                return False, "Timeout after retries"
            logger.warning(f"SMS attempt {attempt+1} timed out, retrying...")
            time.sleep(2 ** attempt)  # 1, 2, 4 seconds backoff

        except requests.RequestException as e:
            detail = e.response.text if e.response else str(e)
            logger.error(f"Failed to send SMS to {user.phone} via TextBee: {detail}")
            return False, detail

    return False, "Unexpected error"