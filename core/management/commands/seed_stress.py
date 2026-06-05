import random
from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import Parent, Student, TeacherProfile, User
from core.models import (
    ActivityLog,
    AttendanceRecord,
    FeePayment,
    MarkEntry,
    NewsAndEvents,
    School,
    SchoolClass,
    SchoolFee,
    Session,
    Term,
    TimetableEntry,
)
from course.models import Subject, SubjectAllocation, Upload, UploadVideo
from payments.models import Invoice
from result.models import FAIL, PASS, PhysicalAssessment, PhysicalAssessmentMark, Result, TakenCourse


FIRST_NAMES = [
    "Lerato", "Neo", "Mpho", "Thabo", "Palesa", "Kabelo", "Naledi", "Refiloe",
    "Tumelo", "Karabo", "Lineo", "Teboho", "Maserame", "Rethabile", "Mokete",
]
LAST_NAMES = [
    "Mokoena", "Molefe", "Theko", "Ramohapi", "Motaung", "Khama", "Ndlovu",
    "Maseko", "Mahlangu", "Motsoeneng", "Radebe", "Mofokeng",
]
SUBJECTS = [
    ("Mathematics", "MATH"),
    ("English Language", "ENG"),
    ("Integrated Science", "SCI"),
    ("History", "HIST"),
    ("Geography", "GEO"),
    ("Business Studies", "BUS"),
    ("Computer Studies", "ICT"),
    ("Agriculture", "AGR"),
    ("Accounting", "ACC"),
    ("Physical Education", "PE"),
    ("Art", "ART"),
    ("Life Skills", "LIFE"),
]
LEVELS = ["F1", "F2", "F3", "F4", "F5"]
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
PASSWORD = "StressTest123!"


class Command(BaseCommand):
    help = "Create bulk dummy data for stress testing."

    def add_arguments(self, parser):
        parser.add_argument("--slug", default="stress-academy", help="School subdomain/slug prefix.")
        parser.add_argument("--students", type=int, default=1000)
        parser.add_argument("--teachers", type=int, default=80)
        parser.add_argument("--classes", type=int, default=20)
        parser.add_argument("--subjects-per-class", type=int, default=8)
        parser.add_argument("--parents", type=int, default=500)
        parser.add_argument("--attendance-days", type=int, default=10)
        parser.add_argument("--uploads-per-subject", type=int, default=2)
        parser.add_argument("--videos-per-subject", type=int, default=1)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the existing stress-test school for this slug before creating data.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])
        slug = slugify(options["slug"]) or "stress-academy"

        if options["reset"]:
            deleted, _ = School.objects.filter(subdomain=slug).delete()
            self.stdout.write(f"Deleted {deleted} existing objects for subdomain '{slug}'.")

        school = self.create_school(slug)
        session, term = self.create_period(school)
        admin = self.create_admin(school, slug)
        teachers = self.create_teachers(school, slug, options["teachers"])
        classes = self.create_classes(school, teachers, options["classes"])
        subjects = self.create_subjects(school, classes, teachers, options["subjects_per_class"])
        students = self.create_students(school, slug, classes, options["students"])
        parents = self.create_parents(school, slug, students, options["parents"])

        self.create_allocations(teachers, subjects, session)
        self.create_course_materials(subjects, options["uploads_per_subject"], options["videos_per_subject"])
        self.create_academic_records(school, students, subjects, session, term, teachers, options["attendance_days"])
        self.create_finance_records(school, students, session, term, admin)
        self.create_news_and_logs(school, options["students"])
        self.create_invoices(admin, teachers, parents)

        self.stdout.write(self.style.SUCCESS("Stress-test seed complete."))
        self.stdout.write(f"School: {school.name} ({school.subdomain})")
        self.stdout.write(f"Admin login: stress_admin_{slug} / {PASSWORD}")
        self.stdout.write(f"Created: {len(students)} students, {len(teachers)} teachers, {len(classes)} classes, {len(subjects)} subjects.")

    def create_school(self, slug):
        school, _ = School.objects.update_or_create(
            subdomain=slug,
            defaults={
                "name": f"{slug.replace('-', ' ').title()} Stress School",
                "slug": slug,
                "registration_number": f"STRESS-{slug.upper()}",
                "email": f"{slug}@example.test",
                "phone": "+26650000000",
                "address": "Stress test campus",
                "status": "active",
                "plan": "unlimited",
                "current_quarter": "Q1",
                "is_active": True,
            },
        )
        return school

    def create_period(self, school):
        session, _ = Session.objects.update_or_create(
            school=school,
            session="2026",
            defaults={"is_current": True, "next_session_begins": timezone.localdate().replace(year=2027)},
        )
        term, _ = Term.objects.update_or_create(
            school=school,
            session=session,
            name="T1",
            defaults={"is_current": True, "next_begins": timezone.localdate() + timezone.timedelta(days=90)},
        )
        return session, term

    def create_admin(self, school, slug):
        username = f"stress_admin_{slug}"
        admin, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "first_name": "Stress",
                "last_name": "Admin",
                "email": f"{username}@example.test",
                "school": school,
                "is_staff": True,
                "is_superuser": True,
                "password": make_password(PASSWORD),
            },
        )
        return admin

    def create_teachers(self, school, slug, count):
        existing = set(User.objects.filter(username__startswith=f"stress_teacher_{slug}_").values_list("username", flat=True))
        users = []
        for index in range(1, count + 1):
            username = f"stress_teacher_{slug}_{index:04d}"
            if username in existing:
                continue
            first, last = self.name_for(index)
            users.append(
                User(
                    username=username,
                    first_name=first,
                    last_name=last,
                    email=f"{username}@example.test",
                    school=school,
                    is_lecturer=True,
                    is_staff=True,
                    password=make_password(PASSWORD),
                    gender=random.choice(["M", "F"]),
                    phone=f"+26658{index:06d}",
                    address="Stress teacher address",
                )
            )
        User.objects.bulk_create(users, batch_size=1000)
        teachers = list(User.objects.filter(school=school, is_lecturer=True, username__startswith=f"stress_teacher_{slug}_"))

        profiles = [
            TeacherProfile(
                user=teacher,
                staff_number=f"STF-{slug}-{idx:04d}",
                qualification=random.choice(["B.Ed", "BSc", "BA", "M.Ed"]),
                specialization=random.choice([title for title, _ in SUBJECTS]),
                is_class_teacher=idx <= 20,
            )
            for idx, teacher in enumerate(teachers, start=1)
            if not hasattr(teacher, "teacher_profile")
        ]
        TeacherProfile.objects.bulk_create(profiles, batch_size=1000, ignore_conflicts=True)
        return teachers

    def create_classes(self, school, teachers, count):
        existing = set(SchoolClass.objects.filter(school=school).values_list("name", flat=True))
        classes = []
        for index in range(1, count + 1):
            level = LEVELS[(index - 1) % len(LEVELS)]
            stream = chr(65 + ((index - 1) % 8))
            name = f"{level} {stream}{((index - 1) // 8) + 1}"
            if name in existing:
                continue
            classes.append(
                SchoolClass(
                    school=school,
                    name=name,
                    level=level,
                    class_teacher=teachers[(index - 1) % len(teachers)] if teachers else None,
                    is_active=True,
                )
            )
        SchoolClass.objects.bulk_create(classes, batch_size=1000)
        return list(SchoolClass.objects.filter(school=school, is_active=True).order_by("id"))

    def create_subjects(self, school, classes, teachers, per_class):
        existing = set(
            Subject.objects.filter(school=school).values_list("class_assigned_id", "slug")
        )
        subjects = []
        for class_index, school_class in enumerate(classes):
            for subject_index, (title, code) in enumerate(SUBJECTS[:per_class], start=1):
                slug = slugify(f"{code}-{school_class.name}")
                if (school_class.id, slug) in existing:
                    continue
                subjects.append(
                    Subject(
                        school=school,
                        class_assigned=school_class,
                        slug=slug,
                        title=title,
                        code=f"{code}{class_index + 1:02d}",
                        summary=f"{title} stress-test subject for {school_class.name}",
                        teacher=teachers[(class_index + subject_index) % len(teachers)] if teachers else None,
                        is_electable=subject_index % 4 == 0,
                    )
                )
        Subject.objects.bulk_create(subjects, batch_size=1000)
        return list(Subject.objects.filter(school=school).select_related("class_assigned", "teacher"))

    def create_students(self, school, slug, classes, count):
        existing = set(User.objects.filter(username__startswith=f"stress_student_{slug}_").values_list("username", flat=True))
        users = []
        for index in range(1, count + 1):
            username = f"stress_student_{slug}_{index:06d}"
            if username in existing:
                continue
            first, last = self.name_for(index)
            users.append(
                User(
                    username=username,
                    first_name=first,
                    last_name=last,
                    email=f"{username}@example.test",
                    school=school,
                    is_student=True,
                    password=make_password(PASSWORD),
                    gender=random.choice(["M", "F"]),
                    phone=f"+26657{index:06d}",
                    address="Stress student address",
                )
            )
        User.objects.bulk_create(users, batch_size=2000)

        student_users = list(
            User.objects.filter(school=school, is_student=True, username__startswith=f"stress_student_{slug}_").order_by("id")
        )
        existing_student_user_ids = set(Student.objects.filter(student__in=student_users).values_list("student_id", flat=True))
        students = []
        for index, user in enumerate(student_users):
            if user.id in existing_student_user_ids:
                continue
            school_class = classes[index % len(classes)]
            students.append(Student(student=user, level=school_class.level, student_class=school_class))
        Student.objects.bulk_create(students, batch_size=2000)
        return list(Student.objects.filter(student__school=school).select_related("student", "student_class").order_by("id"))

    def create_parents(self, school, slug, students, count):
        count = min(count, len(students))
        existing = set(User.objects.filter(username__startswith=f"stress_parent_{slug}_").values_list("username", flat=True))
        users = []
        for index in range(1, count + 1):
            username = f"stress_parent_{slug}_{index:06d}"
            if username in existing:
                continue
            first, last = self.name_for(index + 5000)
            users.append(
                User(
                    username=username,
                    first_name=first,
                    last_name=last,
                    email=f"{username}@example.test",
                    school=school,
                    is_parent=True,
                    password=make_password(PASSWORD),
                    phone=f"+26659{index:06d}",
                    address="Stress parent address",
                )
            )
        User.objects.bulk_create(users, batch_size=2000)

        parent_users = list(User.objects.filter(school=school, is_parent=True, username__startswith=f"stress_parent_{slug}_").order_by("id"))
        existing_parent_user_ids = set(Parent.objects.filter(user__in=parent_users).values_list("user_id", flat=True))
        parents = []
        for index, user in enumerate(parent_users[:count]):
            if user.id in existing_parent_user_ids:
                continue
            parents.append(
                Parent(
                    user=user,
                    student=students[index % len(students)],
                    first_name=user.first_name,
                    last_name=user.last_name,
                    phone=user.phone,
                    email=user.email,
                    relation_ship=random.choice(["Father", "Mother", "Other"]),
                )
            )
        Parent.objects.bulk_create(parents, batch_size=2000)
        return list(Parent.objects.filter(user__school=school).select_related("user", "student"))

    def create_allocations(self, teachers, subjects, session):
        existing_teacher_ids = set(
            SubjectAllocation.objects.filter(teacher__in=teachers, session=session).values_list("teacher_id", flat=True)
        )
        allocations = [
            SubjectAllocation(teacher=teacher, session=session)
            for teacher in teachers
            if teacher.id not in existing_teacher_ids
        ]
        SubjectAllocation.objects.bulk_create(allocations, batch_size=1000)
        allocation_map = {
            allocation.teacher_id: allocation
            for allocation in SubjectAllocation.objects.filter(teacher__in=teachers, session=session)
        }
        subjects_by_teacher = defaultdict(list)
        for subject in subjects:
            if subject.teacher_id:
                subjects_by_teacher[subject.teacher_id].append(subject)
        for teacher_id, teacher_subjects in subjects_by_teacher.items():
            allocation = allocation_map.get(teacher_id)
            if allocation:
                allocation.subjects.set(teacher_subjects)

    def create_course_materials(self, subjects, uploads_per_subject, videos_per_subject):
        uploads = []
        videos = []
        for subject in subjects:
            for index in range(1, uploads_per_subject + 1):
                uploads.append(
                    Upload(
                        subject=subject,
                        title=f"{subject.title} Resource {index}",
                        file=f"course_files/stress/{subject.slug}/resource-{index}.pdf",
                    )
                )
            for index in range(1, videos_per_subject + 1):
                videos.append(
                    UploadVideo(
                        subject=subject,
                        title=f"{subject.title} Video {index}",
                        slug=f"{subject.slug}-video-{index}",
                        summary="Stress-test video placeholder.",
                        video=f"course_videos/stress/{subject.slug}/video-{index}.mp4",
                    )
                )
        Upload.objects.bulk_create(uploads, batch_size=2000, ignore_conflicts=True)
        UploadVideo.objects.bulk_create(videos, batch_size=2000, ignore_conflicts=True)

    def create_academic_records(self, school, students, subjects, session, term, teachers, attendance_days):
        subjects_by_class = defaultdict(list)
        for subject in subjects:
            subjects_by_class[subject.class_assigned_id].append(subject)

        taken_courses = []
        mark_entries = []
        results = []
        assessments = []
        today = timezone.localdate()

        exams_by_class = {}
        from core.models import Exam

        for school_class in {student.student_class for student in students if student.student_class_id}:
            exam, _ = Exam.objects.update_or_create(
                school=school,
                school_class=school_class,
                name=f"{school_class.name} Stress Midterm",
                defaults={
                    "session": session,
                    "term": term,
                    "starts_on": today,
                    "ends_on": today + timezone.timedelta(days=5),
                    "status": "published",
                    "results_published": True,
                },
            )
            exams_by_class[school_class.id] = exam

        for subject in subjects:
            assessments.append(
                PhysicalAssessment(
                    school=school,
                    subject=subject,
                    title=f"{subject.title} Test 1",
                    assessment_type="test",
                    max_marks=100,
                    date_conducted=today,
                    created_by=subject.teacher,
                )
            )
        PhysicalAssessment.objects.bulk_create(assessments, batch_size=2000)
        assessments = list(PhysicalAssessment.objects.filter(school=school, title__endswith="Test 1").select_related("subject"))
        assessment_by_subject = {assessment.subject_id: assessment for assessment in assessments}

        assessment_marks = []
        attendance = []
        for student_index, student in enumerate(students):
            class_subjects = subjects_by_class.get(student.student_class_id, [])
            scores = []
            for subject_index, subject in enumerate(class_subjects):
                assignment = self.score(student_index, subject_index, 55, 100)
                mid_exam = self.score(student_index, subject_index + 1, 45, 100)
                quiz = self.score(student_index, subject_index + 2, 40, 100)
                attendance_score = self.score(student_index, subject_index + 3, 70, 100)
                final_exam = self.score(student_index, subject_index + 4, 35, 100)
                total = (Decimal(assignment + mid_exam) / Decimal("2") * Decimal("0.40")) + (Decimal(final_exam) * Decimal("0.60"))
                grade_comment = PASS if total >= Decimal("45") else FAIL
                scores.append(total)

                taken_courses.append(
                    TakenCourse(
                        school=school,
                        student=student,
                        course=subject,
                        quarter=random.choice(QUARTERS),
                        assignment=assignment,
                        mid_exam=mid_exam,
                        quiz=quiz,
                        attendance=attendance_score,
                        final_exam=final_exam,
                        total=total,
                        grade="D" if total < 50 else "C" if total < 60 else "B" if total < 75 else "A",
                        point=Decimal("0.00"),
                        comment=grade_comment,
                    )
                )
                mark_entries.append(
                    MarkEntry(
                        school=school,
                        student=student,
                        subject=subject,
                        exam=exams_by_class.get(student.student_class_id),
                        continuous_assessment=assignment,
                        exam_mark=final_exam,
                        final_mark=(Decimal(assignment) * Decimal("0.40")) + (Decimal(final_exam) * Decimal("0.60")),
                        status=random.choice(["draft", "approved", "published"]),
                        processed_by=subject.teacher,
                    )
                )
                assessment = assessment_by_subject.get(subject.id)
                if assessment:
                    assessment_marks.append(
                        PhysicalAssessmentMark(
                            assessment=assessment,
                            student=student,
                            marks_obtained=mid_exam,
                            remarks="Stress-test mark",
                            entered_by=subject.teacher,
                        )
                    )
                for day in range(attendance_days):
                    attendance.append(
                        AttendanceRecord(
                            school=school,
                            student=student,
                            school_class=student.student_class,
                            subject=subject,
                            date=today - timezone.timedelta(days=day),
                            status=random.choices(["present", "absent", "late", "excused"], weights=[88, 5, 5, 2])[0],
                            recorded_by=subject.teacher,
                        )
                    )

            if scores:
                average = sum(scores) / Decimal(len(scores))
                results.append(
                    Result(
                        school=school,
                        student=student,
                        session=session.session,
                        quarter="Q1",
                        total_subjects=len(scores),
                        total_points=Decimal("0.00"),
                        average=average,
                        comment=PASS if average >= 45 else FAIL,
                    )
                )

        TakenCourse.objects.bulk_create(taken_courses, batch_size=5000)
        MarkEntry.objects.bulk_create(mark_entries, batch_size=5000, ignore_conflicts=True)
        PhysicalAssessmentMark.objects.bulk_create(assessment_marks, batch_size=5000, ignore_conflicts=True)
        AttendanceRecord.objects.bulk_create(attendance, batch_size=5000, ignore_conflicts=True)
        Result.objects.bulk_create(results, batch_size=5000)

        self.create_timetable(school, subjects, teachers)

    def create_timetable(self, school, subjects, teachers):
        entries = []
        days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        starts = ["08:00", "09:00", "10:15", "11:15", "13:00", "14:00"]
        ends = ["08:50", "09:50", "11:05", "12:05", "13:50", "14:50"]
        grouped = defaultdict(list)
        for subject in subjects:
            grouped[subject.class_assigned_id].append(subject)
        for class_id, class_subjects in grouped.items():
            slot = 0
            for day in days:
                for period, subject in enumerate(class_subjects[: len(starts)]):
                    entries.append(
                        TimetableEntry(
                            school=school,
                            school_class=subject.class_assigned,
                            subject=subject,
                            teacher=subject.teacher or (teachers[slot % len(teachers)] if teachers else None),
                            day=day,
                            start_time=starts[period],
                            end_time=ends[period],
                            room=f"R{class_id}-{period + 1}",
                            is_active=True,
                        )
                    )
                    slot += 1
        TimetableEntry.objects.bulk_create(entries, batch_size=5000, ignore_conflicts=True)

    def create_finance_records(self, school, students, session, term, admin):
        fees = []
        for index, student in enumerate(students):
            amount = Decimal(random.choice([350, 500, 750, 1000]))
            paid = index % 3 == 0
            fees.append(
                SchoolFee(
                    school=school,
                    student=student,
                    session=session,
                    term=term,
                    description="Stress-test tuition",
                    amount_due=amount,
                    discount=Decimal("0.00"),
                    due_date=timezone.localdate() + timezone.timedelta(days=30),
                    status="paid" if paid else "pending",
                )
            )
        SchoolFee.objects.bulk_create(fees, batch_size=5000)
        saved_fees = list(SchoolFee.objects.filter(school=school, description="Stress-test tuition"))
        payments = [
            FeePayment(
                fee=fee,
                amount=fee.amount_due,
                method=random.choice(["cash", "bank", "mobile_money", "card"]),
                reference=f"STRESS-PAY-{fee.id}",
                received_by=admin,
                notes="Stress-test payment",
            )
            for index, fee in enumerate(saved_fees)
            if index % 3 == 0
        ]
        FeePayment.objects.bulk_create(payments, batch_size=5000)

    def create_news_and_logs(self, school, student_count):
        NewsAndEvents.objects.bulk_create(
            [
                NewsAndEvents(
                    school=school,
                    title=f"Stress Announcement {index}",
                    summary=f"Operational message for stress-test cohort of {student_count} students.",
                    posted_as=random.choice(["news", "event"]),
                    target_audience=random.choice(["all", "parents", "students", "teachers"]),
                )
                for index in range(1, 51)
            ],
            batch_size=1000,
        )
        ActivityLog.objects.bulk_create(
            [
                ActivityLog(school=school, message=f"Stress-test activity log entry {index}")
                for index in range(1, 501)
            ],
            batch_size=1000,
        )

    def create_invoices(self, admin, teachers, parents):
        users = [admin] + teachers[:50] + [parent.user for parent in parents[:100]]
        Invoice.objects.bulk_create(
            [
                Invoice(
                    user=user,
                    total=1000,
                    amount=random.choice([250, 400, 750, 1000]),
                    payment_complete=index % 2 == 0,
                    invoice_code=f"STRESS-INV-{user.id}-{index}",
                    payment_method=random.choice(["bank", "mpesa", "ecocash", "stripe", "paypal"]),
                    payment_verified=index % 3 == 0,
                    verification_notes="Stress-test invoice",
                )
                for index, user in enumerate(users, start=1)
            ],
            batch_size=1000,
        )

    def name_for(self, index):
        return FIRST_NAMES[index % len(FIRST_NAMES)], LAST_NAMES[index % len(LAST_NAMES)]

    def score(self, student_index, subject_index, minimum, maximum):
        return Decimal(minimum + ((student_index * 7 + subject_index * 11) % (maximum - minimum + 1)))
