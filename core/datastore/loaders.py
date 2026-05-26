from accounts.models import Student, User
from core.models import SchoolClass, Session, Term
from course.models import Subject

from .engine import DataStore


class SchoolDataLoader:

    @staticmethod
    def load_school(school):

        store = DataStore.get_school_store(school.id)

        # =====================================
        # STUDENTS
        # =====================================

        students = Student.objects.select_related(
            "student",
            "student_class",
        ).filter(
            student__school=school
        )

        for student in students:

            store["students_by_id"][student.id] = student

            store["students_by_username"][
                student.student.username
            ] = student

            class_name = (
                student.student_class.name
                if student.student_class
                else "UNASSIGNED"
            )

            if class_name not in store["students_by_class"]:
                store["students_by_class"][class_name] = []

            store["students_by_class"][class_name].append(student)

        # =====================================
        # SUBJECTS
        # =====================================

        subjects = Subject.objects.select_related(
            "teacher"
        ).filter(
            school=school
        )

        for subject in subjects:

            store["subjects_by_id"][subject.id] = subject
            store["subjects_by_code"][subject.code] = subject

        # =====================================
        # CLASSES
        # =====================================

        classes = SchoolClass.objects.select_related(
            "class_teacher"
        ).filter(
            school=school
        )

        for school_class in classes:
            store["classes_by_id"][school_class.id] = school_class

        # =====================================
        # TEACHERS
        # =====================================

        teachers = User.objects.filter(
            school=school,
            is_lecturer=True,
        )

        for teacher in teachers:
            store["teachers_by_id"][teacher.id] = teacher

        # =====================================
        # CURRENT SESSION
        # =====================================

        store["current_session"] = Session.objects.filter(
            school=school,
            is_current=True,
        ).first()

        # =====================================
        # CURRENT TERM
        # =====================================

        store["current_term"] = Term.objects.filter(
            school=school,
            is_current=True,
        ).first()

@staticmethod
def refresh_student(student):

    store = DataStore.get_school_store(
        student.student.school.id
    )

    store["students_by_id"][student.id] = student