from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from accounts.decorators import lecturer_required
from accounts.models import Student
from course.models import Subject as Course
from result.views import get_current_quarter, save_assessment_mark
from .forms import (
    EssayForm,
    EssayQuestionForm,
    MCQuestionForm,
    MCQuestionFormSet,
    QuestionForm,
    QuizAddForm,
    QUESTION_TYPE_ESSAY,
)
from .models import (
    EXAM_CATEGORY,
    EssayQuestion,
    MCQuestion,
    Progress,
    Question,
    QuestionGrade,
    Quiz,
    Sitting,
)

QUIZ_RESULT_FIELDS = {
    "assignment": "assignment",
    EXAM_CATEGORY: "final_exam",
    "practice": "quiz",
}


def school_scoped_courses(user):
    qs = Course.objects.all()
    school = getattr(user, "school", None)
    if school:
        qs = qs.filter(school=school)
    return qs


def get_school_scoped_course(user, **filters):
    return get_object_or_404(school_scoped_courses(user), **filters)


def school_scoped_quizzes(user):
    qs = Quiz.objects.all()
    school = getattr(user, "school", None)
    if school:
        qs = qs.filter(course__school=school)
    return qs


# ========================================================
# 🎯 QUIZ MANAGEMENT (LECTURER)
# ========================================================

@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizCreateView(CreateView):
    model = Quiz
    form_class = QuizAddForm
    template_name = "quiz/quiz_form.html"

    def get_initial(self):
        initial = super().get_initial()
        initial["course"] = get_school_scoped_course(self.request.user, slug=self.kwargs["slug"])
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = get_school_scoped_course(self.request.user, slug=self.kwargs["slug"])
        context["is_create"] = True
        return context

    def form_valid(self, form):
        form.instance.course = get_school_scoped_course(self.request.user, slug=self.kwargs["slug"])
        with transaction.atomic():
            self.object = form.save()
        if form.cleaned_data.get("question_type") == QUESTION_TYPE_ESSAY:
            return redirect("essay_create", slug=self.kwargs["slug"], quiz_id=self.object.id)
        return redirect("mc_create", slug=self.kwargs["slug"], quiz_id=self.object.id)


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizUpdateView(UpdateView):
    model = Quiz
    form_class = QuizAddForm
    template_name = "quiz/quiz_form.html"

    def get_object(self, queryset=None):
        return get_object_or_404(school_scoped_quizzes(self.request.user), pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = get_school_scoped_course(self.request.user, slug=self.kwargs["slug"])
        context["quiz"] = self.object
        return context

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
        return redirect("quiz_index", self.kwargs["slug"])


@login_required
@lecturer_required
def quiz_delete(request, slug, pk):
    quiz = get_object_or_404(school_scoped_quizzes(request.user), pk=pk)
    if request.method != "POST":
        return render(request, "core/confirm_delete.html", {"object": quiz, "cancel_url": "quiz_index", "cancel_kwargs": {"slug": slug}})
    quiz.delete()
    messages.success(request, "Quiz deleted successfully.")
    return redirect("quiz_index", slug=slug)


@login_required
def quiz_list(request, slug):
    course = get_school_scoped_course(request.user, slug=slug)
    quizzes = Quiz.objects.filter(course=course).order_by("-timestamp")
    completed_exam_ids = []
    if request.user.is_authenticated and request.user.is_student:
        completed_exam_ids = list(
            Sitting.objects.filter(
                user=request.user,
                course=course,
                quiz__category=EXAM_CATEGORY,
                complete=True,
            ).values_list("quiz_id", flat=True)
        )

    return render(request, "quiz/quiz_list.html", {
        "quizzes": quizzes,
        "course": course,
        "completed_exam_ids": completed_exam_ids,
    })


# ========================================================
# ❓ MCQ QUESTION MANAGEMENT
# ========================================================

@method_decorator([login_required, lecturer_required], name="dispatch")
class MCQuestionCreate(CreateView):
    model = MCQuestion
    form_class = MCQuestionForm
    template_name = "quiz/mcquestion_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = get_object_or_404(school_scoped_quizzes(self.request.user), id=self.kwargs["quiz_id"])

        context["course"] = get_school_scoped_course(self.request.user, slug=self.kwargs["slug"])
        context["quiz_obj"] = quiz
        context["quiz_questions_count"] = Question.objects.filter(quiz=quiz).count()

        context["formset"] = (
            MCQuestionFormSet(self.request.POST)
            if self.request.method == "POST"
            else MCQuestionFormSet()
        )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        if not formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()

            quiz = get_object_or_404(school_scoped_quizzes(self.request.user), id=self.kwargs["quiz_id"])
            self.object.quiz.add(quiz)

            formset.instance = self.object
            formset.save()

        if "another" in self.request.POST:
            return redirect("mc_create", slug=self.kwargs["slug"], quiz_id=quiz.id)

        return redirect("quiz_index", slug=self.kwargs["slug"])


@method_decorator([login_required, lecturer_required], name="dispatch")
class EssayQuestionCreate(CreateView):
    model = EssayQuestion
    form_class = EssayQuestionForm
    template_name = "quiz/essayquestion_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = get_object_or_404(school_scoped_quizzes(self.request.user), id=self.kwargs["quiz_id"])
        context["course"] = get_school_scoped_course(self.request.user, slug=self.kwargs["slug"])
        context["quiz_obj"] = quiz
        context["quiz_questions_count"] = Question.objects.filter(quiz=quiz).count()
        return context

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            quiz = get_object_or_404(school_scoped_quizzes(self.request.user), id=self.kwargs["quiz_id"])
            self.object.quiz.add(quiz)

        if "another" in self.request.POST:
            return redirect("essay_create", slug=self.kwargs["slug"], quiz_id=quiz.id)

        return redirect("quiz_index", slug=self.kwargs["slug"])


# ========================================================
# 📊 QUIZ PROGRESS
# ========================================================

@method_decorator([login_required], name="dispatch")
class QuizUserProgressView(TemplateView):
    template_name = "quiz/progress.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        progress, _ = Progress.objects.get_or_create(user=self.request.user)

        context["cat_scores"] = progress.list_all_cat_scores
        context["exams"] = progress.show_exams()
        context["exams_counter"] = context["exams"].count()
        return context


# ========================================================
# 🧠 QUIZ MARKING (LECTURER)
# ========================================================

@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizMarkingList(ListView):
    model = Sitting
    template_name = "quiz/sitting_list.html"

    def get_queryset(self):
        qs = Sitting.objects.filter(complete=True)
        school = getattr(self.request.user, "school", None)
        if school:
            qs = qs.filter(course__school=school)

        if not self.request.user.is_superuser:
            qs = qs.filter(
                Q(course__teacher=self.request.user)
                | Q(course__allocated_subjects__teacher=self.request.user)
                | Q(quiz__course__teacher=self.request.user)
                | Q(quiz__course__allocated_subjects__teacher=self.request.user)
            ).distinct()

        quiz_filter = self.request.GET.get("quiz_filter")
        user_filter = self.request.GET.get("user_filter")

        if quiz_filter:
            qs = qs.filter(quiz__title__icontains=quiz_filter)
        if user_filter:
            qs = qs.filter(user__username__icontains=user_filter)

        return qs


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizMarkingDetail(DetailView):
    model = Sitting
    template_name = "quiz/quiz_marking_detail.html"

    def get_queryset(self):
        qs = super().get_queryset()
        school = getattr(self.request.user, "school", None)
        if school:
            qs = qs.filter(course__school=school)
        if not self.request.user.is_superuser:
            qs = qs.filter(
                Q(course__teacher=self.request.user)
                | Q(course__allocated_subjects__teacher=self.request.user)
                | Q(quiz__course__teacher=self.request.user)
                | Q(quiz__course__allocated_subjects__teacher=self.request.user)
            ).distinct()
        return qs

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()
        qid = request.POST.get("qid")

        if qid:
            try:
                qid = int(qid)
            except (TypeError, ValueError):
                messages.error(request, "Invalid question.")
                return self.get(request, *args, **kwargs)
            question = next(
                (question for question in sitting.get_questions(with_answers=True) if question.id == qid),
                None,
            )
            if question is None:
                messages.error(request, "Question does not belong to this assessment.")
                return self.get(request, *args, **kwargs)
            awarded_marks = request.POST.get("awarded_marks")
            feedback = request.POST.get("feedback", "")

            if awarded_marks not in (None, ""):
                try:
                    sitting.set_question_score(
                        question=question,
                        awarded_marks=awarded_marks,
                        marked_by=request.user,
                        feedback=feedback,
                    )
                    self._sync_result_mark(sitting)
                    messages.success(request, "Question mark saved.")
                except ValueError:
                    messages.error(request, "Enter a valid mark.")
                except Exception as exc:
                    messages.error(request, str(exc))

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        questions = self.object.get_questions(with_answers=True)
        rows = []
        for question in questions:
            grade = self.object.get_question_grade(question)
            rows.append({
                "question": question,
                "grade": grade,
                "user_answer": question.user_answer,
            })
        context["question_rows"] = rows
        return context

    def _sync_result_mark(self, sitting):
        if sitting.has_unmarked_questions or not sitting.user.is_student:
            return

        field_name = QUIZ_RESULT_FIELDS.get(sitting.quiz.category, "quiz")
        student = get_object_or_404(Student, student=sitting.user, student__school=sitting.user.school)
        save_assessment_mark(
            student=student,
            course=sitting.course,
            quarter=get_current_quarter(getattr(sitting.user, "school", None)),
            field_name=field_name,
            mark=sitting.get_percent_correct,
        )


# ========================================================
# 🧪 QUIZ TAKING (STUDENTS)
# ========================================================

@method_decorator([login_required], name="dispatch")
class QuizTake(FormView):
    form_class = QuestionForm
    template_name = "quiz/question.html"
    result_template_name = "quiz/result.html"

    def dispatch(self, request, *args, **kwargs):
        self.course = get_school_scoped_course(request.user, pk=self.kwargs["pk"])

        if not request.user.is_student:
            messages.error(request, "Only students can take assessments.")
            return redirect("quiz_index", slug=self.course.slug)
        self.quiz = get_object_or_404(
            school_scoped_quizzes(request.user),
            slug=self.kwargs["slug"],
            course=self.course,
        )

        if not Question.objects.filter(quiz=self.quiz).exists():
            messages.warning(request, "This quiz has no questions.")
            return redirect("quiz_index", slug=self.course.slug)

        self.sitting = Sitting.objects.user_sitting(request.user, self.quiz, self.course)
        if not self.sitting:
            messages.info(request, "You already completed this exam.")
            return redirect("quiz_index", slug=self.course.slug)

        self.question = self.sitting.get_first_question()
        self.progress = self.sitting.progress()
        return super().dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["quiz"] = self.quiz
        context["course"] = self.course
        context["question"] = self.question
        context["progress"] = self.progress
        context["sitting"] = self.sitting
        context["is_essay_question"] = isinstance(self.question, EssayQuestion)
        context["question_type_label"] = (
            "Short answer / Essay" if context["is_essay_question"] else "Multiple choice"
        )

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["question"] = self.question
        return kwargs

    def get_form_class(self):
        return EssayForm if isinstance(self.question, EssayQuestion) else self.form_class

    def form_valid(self, form):
        self._process_answer(form)

        if not self.sitting.get_first_question():
            return self._final_result()

        return super().get(self.request)

    def _process_answer(self, form):
        progress, _ = Progress.objects.get_or_create(user=self.request.user)
        guess = form.cleaned_data["answers"]

        if isinstance(self.question, EssayQuestion):
            QuestionGrade.objects.update_or_create(
                sitting=self.sitting,
                question=self.question,
                defaults={"awarded_marks": None},
            )
            progress.update_score(self.question, 0, self.question.marks)
        else:
            correct = self.question.check_if_correct(guess)
            awarded_marks = self.question.marks if correct else 0
            self.sitting.set_question_score(self.question, awarded_marks)
            progress.update_score(self.question, awarded_marks, self.question.marks)

        self.sitting.add_user_answer(self.question, guess)
        self.sitting.remove_first_question()

        self.question = self.sitting.get_first_question()
        self.progress = self.sitting.progress()

    def _final_result(self):
        self.sitting.mark_quiz_complete()
        self._sync_result_mark()

        result = {
            "course": self.course,
            "quiz": self.quiz,
            "score": self.sitting.get_current_score,
            "max_score": self.sitting.get_max_score,
            "percent": self.sitting.get_percent_correct,
            "sitting": self.sitting,
        }

        if self.quiz.answers_at_end:
            result["questions"] = self.sitting.get_questions(with_answers=True)

        if not self.sitting.has_unmarked_questions and (
            self.request.user.is_superuser
            or (not self.quiz.exam_paper and self.quiz.category != EXAM_CATEGORY)
        ):
            self.sitting.delete()

        return render(self.request, self.result_template_name, result)

    def _sync_result_mark(self):
        if not self.request.user.is_student:
            return
        if self.sitting.has_unmarked_questions:
            return

        field_name = QUIZ_RESULT_FIELDS.get(self.quiz.category, "quiz")
        student = get_object_or_404(Student, student=self.request.user)
        save_assessment_mark(
            student=student,
            course=self.course,
            quarter=get_current_quarter(getattr(self.request.user, "school", None)),
            field_name=field_name,
            mark=self.sitting.get_percent_correct,
        )
