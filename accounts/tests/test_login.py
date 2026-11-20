from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class EmailLoginTests(TestCase):
    def test_login_error_message_is_rendered_by_shared_layout(self):
        response = self.client.post(
            reverse("login"),
            {"email": "missing@example.com", "password": "wrong-password"},
        )

        self.assertContains(response, "Invalid email or password")
        self.assertContains(response, "alert-danger")

    def test_user_can_log_in_with_email(self):
        User.objects.create_user(
            username="student1",
            email="student@example.com",
            password="correct-password",
            is_student=True,
        )

        response = self.client.post(
            reverse("login"),
            {"email": "STUDENT@example.com", "password": "correct-password"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("student_dashboard"))

    def test_username_is_not_accepted_as_login_identifier(self):
        User.objects.create_user(
            username="student1",
            email="student@example.com",
            password="correct-password",
            is_student=True,
        )

        response = self.client.post(
            reverse("login"),
            {"username": "student1", "password": "correct-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
