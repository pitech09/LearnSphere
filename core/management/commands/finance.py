from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from core.models import SchoolFee, FeePayment, FEE_STATUS_PARTIAL


class FinanceSeeder:

    def create(self, school, users, students, session, term):

        admin = users["admin"]

        for student in students:

            fee, _ = SchoolFee.objects.update_or_create(
                school=school,
                student=student,
                session=session,
                term=term,
                description="Term 1 tuition fees",
                defaults={
                    "amount_due": Decimal("1500.00"),
                    "discount": Decimal("0.00"),
                    "due_date": timezone.localdate() + timedelta(days=14),
                    "status": FEE_STATUS_PARTIAL,
                },
            )

            FeePayment.objects.update_or_create(
                fee=fee,
                reference=f"{school.subdomain.upper()}-{student.id}-T1",
                defaults={
                    "amount": Decimal("500.00"),
                    "paid_on": timezone.localdate(),
                    "method": "cash",
                    "received_by": admin,
                    "notes": "Seed payment",
                },
            )