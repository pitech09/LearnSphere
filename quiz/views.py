from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
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
from course.models import Subject as Course
from .forms import (
    EssayForm,
    MCQuestionForm,
    MCQuestionFormSet,
    QuestionForm,
    QuizAddForm,
)
from .models import (
    EssayQuestion,
    MCQuestion,
    Progress,
    Question,
    Quiz,
    Sitting,
)


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
        initial["course"] = get_object_or_404(Course, slug=self.kwargs["slug"])
        return initial

    def form_valid(self, form):
        form.instance.course = get_object_or_404(Course, slug=self.kwargs["slug"])
        with transaction.atomic():
            self.object = form.save()
        return redirect("mc_create", slug=self.kwargs["slug"], quiz_id=self.object.id)


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizUpdateView(UpdateView):
    model = Quiz
    form_class = QuizAddForm
    template_name = "quiz/quiz_form.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Quiz, pk=self.kwargs["pk"])

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
        return redirect("quiz_index", self.kwargs["slug"])


@login_required
@lecturer_required
def quiz_delete(request, slug, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    quiz.delete()
    messages.success(request, "Quiz deleted successfully.")
    return redirect("quiz_index", slug=slug)


@login_required
def quiz_list(request, slug):
    course = get_object_or_404(Course, slug=slug)
    quizzes = Quiz.objects.filter(course=course).order_by("-timestamp")
    return render(request, "quiz/quiz_list.html", {
        "quizzes": quizzes,
        "course": course
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
        quiz = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])

        context["course"] = get_object_or_404(Course, slug=self.kwargs["slug"])
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

            quiz = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])
            self.object.quiz.add(quiz)

            formset.instance = self.object
            formset.save()

        if "another" in self.request.POST:
            return redirect("mc_create", slug=self.kwargs["slug"], quiz_id=quiz.id)

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
    template_name = "quiz/quiz_marking_list.html"

    def get_queryset(self):
        qs = Sitting.objects.filter(complete=True)

        if not self.request.user.is_superuser:
            qs = qs.filter(
                quiz__course__allocated_subjects__teacher=self.request.user
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

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()
        qid = request.POST.get("qid")

        if qid:
            question = Question.objects.get_subclass(id=int(qid))

            if int(qid) in sitting.get_incorrect_questions:
                sitting.remove_incorrect_question(question)
            else:
                sitting.add_incorrect_question(question)

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = self.object.get_questions(with_answers=True)
        return context


# ========================================================
# 🧪 QUIZ TAKING (STUDENTS)
# ========================================================

@method_decorator([login_required], name="dispatch")
class QuizTake(FormView):
    form_class = QuestionForm
    template_name = "quiz/question.html"
    result_template_name = "quiz/result.html"

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, slug=self.kwargs["slug"])
        self.course = get_object_or_404(Course, pk=self.kwargs["pk"])

        if not Question.objects.filter(quiz=self.quiz).exists():
            messages.warning(request, "This quiz has no questions.")
            return redirect("quiz_index", slug=self.course.slug)

        self.sitting = Sitting.objects.user_sitting(request.user, self.quiz, self.course)
        print("SITTING:", self.sitting)
        if not self.sitting:
            messages.info(request, "You already completed this quiz.")
            return redirect("quiz_index", slug=self.course.slug)

        self.question = self.sitting.get_first_question()
        print("QUESTION:", self.question)
        self.progress = self.sitting.progress()
        print("PROGRESS:", self.progress)
        return super().dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["quiz"] = self.quiz
        context["course"] = self.course
        context["question"] = self.question
        context["progress"] = self.progress
        context["sitting"] = self.sitting

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

        correct = self.question.check_if_correct(guess)

        if correct:
            self.sitting.add_to_score(1)
            progress.update_score(self.question, 1, 1)
        else:
            self.sitting.add_incorrect_question(self.question)
            progress.update_score(self.question, 0, 1)

        self.sitting.add_user_answer(self.question, guess)
        self.sitting.remove_first_question()

        self.question = self.sitting.get_first_question()
        self.progress = self.sitting.progress()

    def _final_result(self):
        self.sitting.mark_quiz_complete()

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

        if not self.quiz.exam_paper or self.request.user.is_superuser:
            self.sitting.delete()

        return render(self.request, self.result_template_name, result)