from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from accounts.mixins import AdminOrAccountantMixin, SessionAuthenticatedMixin, ViewerReadOnlyMixin
from reports.services import paid_status_q
from transactions.models import FlowType

from .forms import ProjectForm
from .models import Project


class ProjectListView(ViewerReadOnlyMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        qs = (
            Project.objects.annotate(
                total_income_paid=Coalesce(
                    Sum(
                        "transactions__total_amount",
                        filter=Q(transactions__flow_type=FlowType.IN)
                        & paid_status_q("transactions__"),
                    ),
                    Value(Decimal("0")),
                    output_field=DecimalField(max_digits=18, decimal_places=2),
                ),
                total_expense=Coalesce(
                    Sum(
                        "transactions__total_amount",
                        filter=Q(transactions__flow_type=FlowType.OUT),
                    ),
                    Value(Decimal("0")),
                    output_field=DecimalField(max_digits=18, decimal_places=2),
                ),
            )
            .annotate(
                net_profit_line=ExpressionWrapper(
                    F("contract_value_excl_vat")
                    - Coalesce(F("total_expense"), Value(Decimal("0"))),
                    output_field=DecimalField(max_digits=18, decimal_places=2),
                )
            )
            .order_by("reference_number")
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(reference_number__icontains=q)
                | Q(name__icontains=q)
                | Q(client_name__icontains=q)
                | Q(notes__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filters"] = {"q": self.request.GET.get("q", "")}
        for p in ctx["object_list"]:
            ti = p.total_income_paid or Decimal("0")
            if p.contract_incl_vat is not None:
                p.remaining_display = p.contract_incl_vat - ti
            else:
                p.remaining_display = None
        return ctx


class ProjectDetailView(SessionAuthenticatedMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        ref = self.kwargs.get("reference_number")
        if ref:
            return get_object_or_404(queryset, reference_number__iexact=ref.strip())
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        p = self.object
        qs = p.transactions.select_related("project").order_by("-date", "-pk")
        ctx["transactions"] = qs[:100]
        ti = (
            p.transactions.filter(flow_type=FlowType.IN)
            .filter(paid_status_q())
            .aggregate(s=Sum("total_amount"))["s"]
            or Decimal("0")
        )
        te = (
            p.transactions.filter(flow_type=FlowType.OUT).aggregate(s=Sum("total_amount"))[
                "s"
            ]
            or Decimal("0")
        )
        ctx["total_income_paid"] = ti
        ctx["total_expense"] = te
        if p.contract_value_excl_vat is not None:
            ctx["net_profit"] = p.contract_value_excl_vat - te
        else:
            ctx["net_profit"] = None
        if p.contract_incl_vat is not None:
            ctx["remaining_display"] = p.contract_incl_vat - ti
        else:
            ctx["remaining_display"] = None
        return ctx


class ProjectCreateView(AdminOrAccountantMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_url = reverse_lazy("projects:list")


class ProjectUpdateView(AdminOrAccountantMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_url = reverse_lazy("projects:list")


class ProjectDeleteView(AdminOrAccountantMixin, DeleteView):
    model = Project
    template_name = "projects/project_confirm_delete.html"
    success_url = reverse_lazy("projects:list")
