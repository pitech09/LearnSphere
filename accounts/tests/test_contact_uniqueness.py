from django.db import IntegrityError
from django.test import TestCase

from accounts.models import User


class UserContactUniquenessTests(TestCase):
    def test_email_is_unique_case_insensitively(self):
        User.objects.create_user(
            username="first",
            email="person@example.com",
            password="password",
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="second",
                email="PERSON@EXAMPLE.COM",
                password="password",
            )

    def test_phone_is_unique_after_common_formatting_is_removed(self):
        User.objects.create_user(
            username="first",
            phone="+266 585-38173",
            password="password",
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="second",
                phone="+26658538173",
                password="password",
            )
