from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Seed initial users (admin, lecturers, students)"

    def handle(self, *args, **kwargs):

        users = [
            {
                "username": "admin",
                "email": "admin@skylearn.com",
                "password": "admin12345",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "lecturer1",
                "email": "lecturer@skylearn.com",
                "password": "lecturer123",
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "username": "student1",
                "email": "student@skylearn.com",
                "password": "student123",
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        for data in users:
            if User.objects.filter(username=data["username"]).exists():
                self.stdout.write(self.style.WARNING(
                    f"User {data['username']} already exists"
                ))
                continue

            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
            )

            user.is_staff = data["is_staff"]
            user.is_superuser = data["is_superuser"]
            user.save()

            self.stdout.write(self.style.SUCCESS(
                f"Created user: {data['username']}"
            ))
