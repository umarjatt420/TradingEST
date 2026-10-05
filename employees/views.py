from django.db.models import Count
from django.db.models.functions import Length
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from accounts.mixins import AccountantOrAdminRequiredMixin, AdminOrAccountantMixin

from .forms import EmployeeForm
from .models import Employee
from .services import employees_with_paid_on


class EmployeeListView(AccountantOrAdminRequiredMixin, ListView):
    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        return employees_with_paid_on(
            Employee.objects.annotate(name_len=Length("name"))
        ).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["totals"] = Employee.objects.aggregate(n=Count("id"))
        return ctx


class EmployeeDetailView(AccountantOrAdminRequiredMixin, DetailView):
    model = Employee
    template_name = "employees/employee_detail.html"
    context_object_name = "employee"

    def get_queryset(self):
        return employees_with_paid_on(super().get_queryset())


class EmployeeCreateView(AdminOrAccountantMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employees:list")


class EmployeeUpdateView(AdminOrAccountantMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employees:list")


class EmployeeDeleteView(AdminOrAccountantMixin, DeleteView):
    model = Employee
    template_name = "employees/employee_confirm_delete.html"
    success_url = reverse_lazy("employees:list")
