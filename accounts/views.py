import logging

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django_filters.views import FilterView
from urllib3 import request
from xhtml2pdf import pisa
from django.contrib.auth import authenticate, login
from accounts.decorators import admin_required
from accounts.filters import LecturerFilter, StudentFilter
from accounts.forms import (
    ParentAddForm,
    ProfileUpdateForm,
    SchoolSignupForm,
    StaffAddForm,
    StudentAddForm,
)
from accounts.models import Parent, Student, User
from accounts.utils import generate_password, send_new_account_sms
from core.models import SCHOOL_PLAN_UNLIMITED, School, Session, Term
from course.models import Subject
from result.models import TakenCourse
from django.utils.http import url_has_allowed_host_and_scheme

logger = logging.getLogger(__name__)

# ########################################################
# Utility Functions
# ########################################################


def render_to_pdf(template_name, context):
    """Render a given template to PDF format."""
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="profile.pdf"'
    template = render_to_string(template_name, context)
    pdf = pisa.CreatePDF(template, dest=response)
    if pdf.err:
        return HttpResponse("We had some problems generating the PDF")
    return response


def school_scoped_users(request, **filters):
    qs = User.objects.filter(**filters)
    school = getattr(request.user, "school", None)
    if school:
        qs = qs.filter(school=school)
    return qs


# ########################################################
# Authentication and Registration
# ########################################################


def validate_username(request):
    username = request.GET.get("username", None)
    data = {"is_taken": User.objects.filter(username__iexact=username).exists()}
    return JsonResponse(data)

def logout_view(request):
    logout(request)
    return redirect("login")


def register(request):
    if request.method == "POST":
        form = StudentAddForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully.")
            return redirect("login")
        messages.error(
            request, "Something is not correct, please fill all fields correctly."
        )
    else:
        form = StudentAddForm()
    return render(request, "registration/register.html", {"form": form})


def school_signup(request):
    if request.method == "POST":
        form = SchoolSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Your school workspace is ready.")
            return redirect("dashboard")
        messages.error(request, "Please correct the highlighted fields.")
    else:
        form = SchoolSignupForm()
    return render(request, "registration/school_signup.html", {"form": form})


from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import User


def custom_login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("username")
        password = request.POST.get("password")
        next_url = request.POST.get("next") or request.GET.get("next")

        user_obj = None

        # 🔥 STEP 1: Try username first
        try:
            user_obj = User.objects.get(username=identifier)
        except User.DoesNotExist:
            pass

        # 🔥 STEP 2: Try email fallback
        if not user_obj:
            try:
                user_obj = User.objects.get(email=identifier)
            except User.DoesNotExist:
                pass

        # 🔥 STEP 3: Resolve to username
        if user_obj:
            identifier = user_obj.username

        user = authenticate(request, username=identifier, password=password)

        if user is not None:
            login(request, user)

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            if user.is_student:
                return redirect("student_dashboard")

            if user.is_lecturer:
                return redirect("teacher_dashboard")

            if user.is_superuser and user.school_id:
                return redirect("principal_dashboard")

            return redirect("dashboard")

        messages.error(request, "Invalid ID or Password")

    return render(request, "registration/login.html", {"next": request.GET.get("next", "")})

def health_check_view(request):
    return render(request, "core/health_check.html", {
        "status": "OK",
        "message": "The application is running smoothly!"
    })


# ########################################################
# Profile Views
# ########################################################


@login_required
def profile(request):
    """Show profile of the current user."""
    current_session = Session.objects.filter(is_current=True, school=request.user.school).first()
    current_semester = Term.objects.filter(
        is_current=True, session=current_session, school=request.user.school
    ).first()

    context = {
        "title": request.user.get_full_name,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if request.user.is_lecturer:

        courses = Subject.objects.filter(teacher_id=request.user.id, school=request.user.school)

        context.update({
            "user_type": "Lecturer",
            "courses": courses,
        })

    if request.user.is_student:
        student = get_object_or_404(Student, student__pk=request.user.id, student__school=request.user.school)
        parent = Parent.objects.filter(student=student).first()
        courses = TakenCourse.objects.filter(
            student__student__id=request.user.id,
            school=request.user.school,
        )
        context.update(
            {
                "parent": parent,
                "courses": courses,
                "level": student.level,
            }
        )
        return render(request, "accounts/profile.html", context)

    # For superuser or other staff
    staff = school_scoped_users(request, is_lecturer=True)
    context["staff"] = staff
    return render(request, "accounts/profile.html", context)


@login_required
@admin_required
def profile_single(request, user_id):
    """Show profile of any selected user."""
    if request.user.id == user_id:
        return redirect("profile")

    current_session = Session.objects.filter(is_current=True, school=request.user.school).first()
    current_semester = Term.objects.filter(
        is_current=True, session=current_session, school=request.user.school
    ).first()
    user = get_object_or_404(school_scoped_users(request), pk=user_id)

    context = {
        "title": user.get_full_name,
        "user": user,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if user.is_lecturer:
        courses = Subject.objects.filter(
            allocated_subjects__teacher__pk=user_id,
            school=user.school,
        )
        context.update(
            {
                "user_type": "Lecturer",
                "courses": courses,
            }
        )
    elif user.is_student:
        student = get_object_or_404(Student, student__pk=user_id, student__school=user.school)
        courses = TakenCourse.objects.filter(
            student__student__id=user_id,
            school=user.school,
        )
        context.update(
            {
                "user_type": "Student",
                "courses": courses,
                "student": student,
            }
        )
    else:
        context["user_type"] = "Superuser"

    if request.GET.get("download_pdf"):
        return render_to_pdf("pdf/profile_single.html", context)

    return render(request, "accounts/profile_single.html", context)


@login_required
@admin_required
def admin_panel(request):
    return render(request, "setting/admin_panel.html", {"title": "Admin Panel"})


# ########################################################
# Settings Views
# ########################################################


@login_required
def profile_update(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, "setting/profile_info_change.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("profile")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "setting/password_change.html", {"form": form})


# ########################################################
# Staff (Lecturer) Views
# ########################################################


@login_required
@admin_required
def staff_add_view(request):
    if request.method == "POST":
        form = StaffAddForm(request.POST)
        if form.is_valid():
            form.instance.school = request.user.school
            lecturer = form.save()
            full_name = lecturer.get_full_name
            phone = lecturer.phone
            raw_password = request.POST.get("password1")
            if not raw_password:
                raw_password = generate_password()
                lecturer.set_password(raw_password)
                lecturer.save(update_fields=["password"])
            send_new_account_sms(lecturer, raw_password)
            messages.success(
                request,
                f"Account for lecturer {full_name} has been created. "
                f"Login credentials will be sent by SMS to {phone} within a minute.",
            )
            return redirect("lecturer_list")
    else:
        form = StaffAddForm()
    return render(
        request, "accounts/add_staff.html", {"title": "Add Lecturer", "form": form}
    )


@login_required
@admin_required
def edit_staff(request, pk):
    lecturer = get_object_or_404(school_scoped_users(request, is_lecturer=True), pk=pk)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=lecturer)
        if form.is_valid():
            form.save()
            full_name = lecturer.get_full_name
            messages.success(request, f"Lecturer {full_name} has been updated.")
            return redirect("lecturer_list")
        messages.error(request, "Please correct the error below.")
    else:
        form = ProfileUpdateForm(instance=lecturer)
    return render(
        request, "accounts/edit_lecturer.html", {"title": "Edit Lecturer", "form": form}
    )


@method_decorator([login_required, admin_required], name="dispatch")
class LecturerFilterView(FilterView):
    filterset_class = LecturerFilter
    template_name = "accounts/lecturer_list.html"
    paginate_by = 10

    def get_queryset(self):
        qs = User.objects.select_related("school").filter(is_lecturer=True)
        school = getattr(self.request.user, "school", None)
        if school:
            qs = qs.filter(school=school)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lecturers"
        return context


@login_required
@admin_required
def render_lecturer_pdf_list(request):
    lecturers = User.objects.select_related("school").filter(is_lecturer=True)
    if request.user.school:
        lecturers = lecturers.filter(school=request.user.school)
    template_path = "pdf/lecturer_list.html"
    context = {"lecturers": lecturers}
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="lecturers_list.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f"We had some errors <pre>{html}</pre>")
    return response


@login_required
@admin_required
def delete_staff(request, pk):
    lecturer = get_object_or_404(school_scoped_users(request, is_lecturer=True), pk=pk)
    full_name = lecturer.get_full_name
    if request.method != "POST":
        return render(request, "core/confirm_delete.html", {"object": lecturer, "cancel_url": "lecturer_list"})
    lecturer.delete()
    messages.success(request, f"Lecturer {full_name} has been deleted.")
    return redirect("lecturer_list")


# ########################################################
# Student Views
# ########################################################
@login_required
@admin_required
def student_add_view(request):
    if request.method == "POST":
        form = StudentAddForm(request.POST, school=request.user.school)

        if form.is_valid():
            # Enforce student limit based on school plan
            school = getattr(request.user, "school", None)
            if school and not school.is_unlimited:
                current_student_count = User.objects.filter(school=school, is_student=True).count()
                if current_student_count >= school.max_students:
                    messages.error(
                        request,
                        f"Student limit reached ({current_student_count}/{school.max_students}). "
                        f"Please upgrade your plan to add more students."
                    )
                    return render(
                        request,
                        "accounts/add_student.html",
                        {"title": "Add Student", "form": form}
                    )

            form.instance.school = request.user.school
            student = form.save()

            full_name = student.get_full_name
            phone = student.phone

            raw_password = request.POST.get("password1")

            send_new_account_sms(student, raw_password)

            messages.success(
                request,
                f"Account for {full_name} created successfully. "
                f"Login credentials sent by SMS to {phone}."
            )

            return redirect("student_list")
        logger.info("Student add form failed validation for school_id=%s", request.user.school_id)
        messages.error(request, "Correct the error(s) below.")

    else:
        form = StudentAddForm(school=request.user.school)

    return render(
        request,
        "accounts/add_student.html",
        {"title": "Add Student", "form": form}
    )

@login_required
@admin_required
def edit_student(request, pk):
    student_user = get_object_or_404(school_scoped_users(request, is_student=True), pk=pk)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=student_user)
        if form.is_valid():
            form.save()
            full_name = student_user.get_full_name
            messages.success(request, f"Student {full_name} has been updated.")
            return redirect("student_list")
        messages.error(request, "Please correct the error below.")
    else:
        form = ProfileUpdateForm(instance=student_user)
    return render(
        request, "accounts/edit_student.html", {"title": "Edit Student", "form": form}
    )


@method_decorator([login_required, admin_required], name="dispatch")
class StudentListView(FilterView):
    filterset_class = StudentFilter
    template_name = "accounts/student_list.html"
    paginate_by = 10

    def get_queryset(self):
        qs = Student.objects.select_related("student", "student_class")
        school = getattr(self.request.user, "school", None)
        if school:
            qs = qs.filter(student__school=school)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Students"
        return context


@login_required
@admin_required
def render_student_pdf_list(request):
    students = Student.objects.select_related("student", "student_class")
    if request.user.school:
        students = students.filter(student__school=request.user.school)
    template_path = "pdf/student_list.html"
    context = {"students": students}
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="students_list.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f"We had some errors <pre>{html}</pre>")
    return response


@login_required
@admin_required
def delete_student(request, pk):
    students = Student.objects.select_related("student", "student_class")
    if request.user.school:
        students = students.filter(student__school=request.user.school)
    student = get_object_or_404(students, pk=pk)
    full_name = student.student.get_full_name
    if request.method != "POST":
        return render(request, "core/confirm_delete.html", {"object": student, "cancel_url": "student_list"})
    student.delete()
    messages.success(request, f"Student {full_name} has been deleted.")
    return redirect("student_list")


# ########################################################
# Parent Views
# ########################################################


@method_decorator([login_required, admin_required], name="dispatch")
class ParentAdd(CreateView):
    model = Parent
    form_class = ParentAddForm
    template_name = "accounts/parent_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = self.request.user.school
        return kwargs

    def form_valid(self, form):
        form.instance.school = self.request.user.school
        messages.success(self.request, "Parent added successfully.")
        return super().form_valid(form)
