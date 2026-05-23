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
<<<<<<< HEAD
    SchoolSignupForm,
=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
    StaffAddForm,
    StudentAddForm,
)
from accounts.models import Parent, Student, User
<<<<<<< HEAD
from accounts.utils import send_new_account_email
=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
from core.models import Session, Term
from course.models import Subject
from result.models import TakenCourse

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

<<<<<<< HEAD
=======
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # 🔀 Redirect based on role
            if user.is_superuser:
                return redirect('admin:index')
            elif hasattr(user, 'profile') and user.profile.role == 'teacher':
                return redirect('dashboard')
            else:
                return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')

>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e

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


<<<<<<< HEAD
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

        print("LOGIN INPUT:", identifier)

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

        print("AUTH RESULT:", user)

        if user is not None:
            login(request, user)

            # role routing
            if hasattr(user, "is_student") and user.is_student:
                return redirect("student_dashboard")

            if hasattr(user, "is_lecturer") and user.is_lecturer:
                return redirect("lecturer_dashboard")

            return redirect("dashboard")

        messages.error(request, "Invalid ID or Password")

    return render(request, "registration/login.html")

=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
# ########################################################
# Profile Views
# ########################################################


<<<<<<< HEAD

=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
@login_required
def profile(request):
    """Show profile of the current user."""
    current_session = Session.objects.filter(is_current=True).first()
    current_semester = Term.objects.filter(
        is_current=True, session=current_session
    ).first()

    context = {
        "title": request.user.get_full_name,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if request.user.is_lecturer:

        courses = Subject.objects.filter(teacher_id=request.user.id)

        print(courses)
        print(type(request.user))
        print(request.user.__class__) 
        context.update({
            "user_type": "Lecturer",
            "courses": courses,
        })

    if request.user.is_student:
        student = get_object_or_404(Student, student__pk=request.user.id)
        parent = Parent.objects.filter(student=student).first()
        courses = TakenCourse.objects.filter(
            student__student__id=request.user.id
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
    staff = User.objects.filter(is_lecturer=True)
    context["staff"] = staff
    return render(request, "accounts/profile.html", context)


@login_required
@admin_required
def profile_single(request, user_id):
    """Show profile of any selected user."""
    if request.user.id == user_id:
        return redirect("profile")

    current_session = Session.objects.filter(is_current=True).first()
    current_semester = Term.objects.filter(
        is_current=True, session=current_session
    ).first()
    user = get_object_or_404(User, pk=user_id)

    context = {
        "title": user.get_full_name,
        "user": user,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if user.is_lecturer:
        courses = Subject.objects.filter(
            allocated_subjects__teacher__pk=user_id
        )
        context.update(
            {
                "user_type": "Lecturer",
                "courses": courses,
            }
        )
    elif user.is_student:
        student = get_object_or_404(Student, student__pk=user_id)
        courses = TakenCourse.objects.filter(
            student__student__id=user_id
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
<<<<<<< HEAD
            form.instance.school = request.user.school
=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
            lecturer = form.save()
            full_name = lecturer.get_full_name
            email = lecturer.email
            messages.success(
                request,
                f"Account for lecturer {full_name} has been created. "
                f"An email with account credentials will be sent to {email} within a minute.",
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
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
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
<<<<<<< HEAD
    template_name = "accounts/lecturer_list.html"
    paginate_by = 10

    def get_queryset(self):
        qs = User.objects.filter(is_lecturer=True)
        school = getattr(self.request.user, "school", None)
        if school:
            qs = qs.filter(school=school)
        return qs

=======
    queryset = User.objects.filter(is_lecturer=True)
    template_name = "accounts/lecturer_list.html"
    paginate_by = 10

>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lecturers"
        return context


@login_required
@admin_required
def render_lecturer_pdf_list(request):
    lecturers = User.objects.filter(is_lecturer=True)
<<<<<<< HEAD
    if request.user.school:
        lecturers = lecturers.filter(school=request.user.school)
=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
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
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
    full_name = lecturer.get_full_name
    lecturer.delete()
    messages.success(request, f"Lecturer {full_name} has been deleted.")
    return redirect("lecturer_list")


# ########################################################
# Student Views
# ########################################################
<<<<<<< HEAD
=======


>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
@login_required
@admin_required
def student_add_view(request):
    if request.method == "POST":
<<<<<<< HEAD
        form = StudentAddForm(request.POST, school=request.user.school)

        if form.is_valid():
            form.instance.school = request.user.school
            student = form.save()

            full_name = student.get_full_name
            email = student.email

            # 🔐 IMPORTANT: retrieve password ONLY if your form generates it
            raw_password = request.POST.get("password1", "1234")

            send_new_account_email(student, raw_password)

            messages.success(
                request,
                f"Account for {full_name} created successfully. "
                f"Login credentials sent to {email}."
            )

            return redirect("student_list")
        print("❌ FORM INVALID")
        print(form.errors)              # 🔥 THIS IS WHAT YOU NEED
        print(form.non_field_errors())  # 🔥 extra hidden errors

        messages.error(request, "Correct the error(s) below.")
        print("form not valid")

    else:
        form = StudentAddForm(school=request.user.school)

    return render(
        request,
        "accounts/add_student.html",
        {"title": "Add Student", "form": form}
    )

=======
        form = StudentAddForm(request.POST)
        print(form)
        if form.is_valid():
            student = form.save()
            full_name = student.get_full_name
            email = student.email
            messages.success(
                request,
                f"Account for {full_name} has been created. "
                f"An email with account credentials will be sent to {email} within a minute.",
            )
            return redirect("student_list")
        messages.error(request, "Correct the error(s) below.")
        print("form not valid")
    else:
        form = StudentAddForm()
    return render(
        request, "accounts/add_student.html", {"title": "Add Student", "form": form}
    )


>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
@login_required
@admin_required
def edit_student(request, pk):
    student_user = get_object_or_404(User, is_student=True, pk=pk)
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
<<<<<<< HEAD
=======
    queryset = Student.objects.all()
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
    filterset_class = StudentFilter
    template_name = "accounts/student_list.html"
    paginate_by = 10

<<<<<<< HEAD
    def get_queryset(self):
        qs = Student.objects.all()
        school = getattr(self.request.user, "school", None)
        if school:
            qs = qs.filter(student__school=school)
        return qs

=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Students"
        return context


@login_required
@admin_required
def render_student_pdf_list(request):
    students = Student.objects.all()
<<<<<<< HEAD
    if request.user.school:
        students = students.filter(student__school=request.user.school)
=======
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
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
    student = get_object_or_404(Student, pk=pk)
    full_name = student.student.get_full_name
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

<<<<<<< HEAD
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = self.request.user.school
        return kwargs

    def form_valid(self, form):
        form.instance.school = self.request.user.school
=======
    def form_valid(self, form):
>>>>>>> 4ae6c4e0707577dffe76510a27cd84e73b1a664e
        messages.success(self.request, "Parent added successfully.")
        return super().form_valid(form)
