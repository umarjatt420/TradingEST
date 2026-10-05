from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, View
from django.views.generic.edit import CreateView, UpdateView

from .forms import LoginForm, SignupForm, UserCreateForm, UserUpdateForm
from .mixins import AdminOnlyMixin
from .models import Role, User


class SignupView(FormView):
    template_name = "accounts/signup.html"
    form_class = SignupForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("reports:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        User.objects.create_user(
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            full_name=form.cleaned_data["full_name"],
            role=Role.ADMIN,
        )
        messages.success(
            self.request,
            "Your administrator account is ready. Sign in to continue.",
        )
        return redirect("accounts:login")


class LoginView(FormView):
    template_name = "accounts/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("reports:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(
            self.request,
            email=email,
            password=password,
        )
        if user is None:
            form.add_error(None, "Invalid email or password.")
            return self.form_invalid(form)
        if not user.is_active:
            form.add_error(None, "This account is disabled.")
            return self.form_invalid(form)
        login(self.request, user)
        return redirect(self.get_success_url())


class LogoutView(View):
    """Session logout — POST only for CSRF safety."""

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("accounts:login")


class UserListView(AdminOnlyMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return (
            User.objects.only(
                "id", "email", "full_name", "role", "is_active", "date_joined"
            )
            .order_by("email")
        )


class UserCreateView(AdminOnlyMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")


class UserUpdateView(AdminOnlyMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")
