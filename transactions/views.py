import json

from django.db.models import Count, F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from accounts.mixins import (
    AccountantOrAdminRequiredMixin,
    AdminOrAccountantMixin,
    SessionAuthenticatedMixin,
    ViewerReadOnlyMixin,
)

from .category_utils import ensure_category_exists, normalize_category_name
from .forms import LegacyPayableForm, TransactionForm
from .models import LegacyPayable, Transaction


class TransactionListView(ViewerReadOnlyMixin, ListView):
    model = Transaction
    template_name = "transactions/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 50

    def get_queryset(self):
        qs = (
            Transaction.objects.select_related("project")
            .annotate(
                project_name=F("project__name"),
            )
            .order_by("-date", "-pk")
        )
        date_filter = self.request.GET.get("date", "").strip()
        flow_type = self.request.GET.get("flow_type", "").strip()
        category_filter = self.request.GET.get("category", "").strip()  # <--- Added
        
        if date_filter:
            qs = qs.filter(date=date_filter)
        if flow_type:
            qs = qs.filter(flow_type=flow_type)
        if category_filter:                                             # <--- Added
            qs = qs.filter(category=category_filter)
        
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        filtered_qs = self.get_queryset()
        agg = filtered_qs.aggregate(
            total_lines=Count("id"),
            sum_excl=Sum("amount_excl_vat"),
            sum_total=Sum("total_amount"),
        )

        date_val = self.request.GET.get("date", "").strip()
        flow_val = self.request.GET.get("flow_type", "").strip()
        cat_val = self.request.GET.get("category", "").strip()         # <--- Added

        ctx["filters"] = {
            "date": date_val,
            "flow_type": flow_val,
            "category": cat_val,                                       # <--- Added
        }
        ctx["ledger_totals"] = agg
        ctx["filters_active"] = bool(date_val or flow_val or cat_val)   # <--- Updated

        ctx["account_breakdown"] = (
            filtered_qs.values("account")
            .annotate(lines=Count("id"), sum_excl=Sum("amount_excl_vat"))
            .order_by("account")
        )

        # Collect all unique categories to populate the dropdown menu
        categories = list(
            Transaction.objects.exclude(category__isnull=True)
            .exclude(category="")
            .values_list("category", flat=True)
            .distinct()
            .order_by("category")
        )
        try:
            from .models import TransactionCategory
            db_cats = list(TransactionCategory.objects.values_list("name", flat=True))
            categories = sorted(list(set(categories + db_cats)))
        except Exception:
            pass
        ctx["categories"] = categories                                 # <--- Added

        from .display_labels import transaction_field_labels

        ctx["labels"] = transaction_field_labels()
        return ctx

    def get(self, request, *args, **kwargs):
        if "export" in request.GET:
            return self.export_excel()
        return super().get(request, *args, **kwargs)

    def export_excel(self):
        import openpyxl
        from django.http import HttpResponse

        qs = self.get_queryset()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Transactions"

        from .display_labels import transaction_field_labels
        labels = transaction_field_labels()

        headers = [
            labels.get("project_reference", "Project Reference"),
            labels.get("date", "Date"),
            labels.get("flow_type", "Flow Type"),
            labels.get("payment_status", "Payment Status"),
            labels.get("amount_excl_vat", "Amount Excl. VAT"),
            labels.get("tax_amount", "Tax Amount"),
            labels.get("total_amount", "Total Amount"),
            labels.get("account", "Account"),
            labels.get("category", "Category"),
            labels.get("project", "Project"),
            labels.get("party_name", "Party Name")
        ]

        ws.append(headers)

        for t in qs:
            ws.append([
                t.project.reference_number if t.project else "—",
                t.date.strftime("%Y-%m-%d") if t.date else "",
                t.flow_type,
                t.payment_status,
                float(t.amount_excl_vat) if t.amount_excl_vat is not None else 0.0,
                float(t.tax_amount) if t.tax_amount is not None else 0.0,
                float(t.total_amount) if t.total_amount is not None else 0.0,
                t.account,
                t.category,
                t.project.name if t.project else "",
                t.party_name
            ])

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="transactions.xlsx"'
        wb.save(response)
        return response


class TransactionDetailView(SessionAuthenticatedMixin, DetailView):
    model = Transaction
    template_name = "transactions/transaction_detail.html"
    context_object_name = "transaction"

    def get_context_data(self, **kwargs):
        from .display_labels import transaction_field_labels

        ctx = super().get_context_data(**kwargs)
        ctx["labels"] = transaction_field_labels()
        return ctx

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        ref = self.kwargs.get("reference_number")
        if ref:
            return get_object_or_404(queryset, reference_number__iexact=ref.strip())
        return super().get_object(queryset)

    def get_queryset(self):
        return Transaction.objects.select_related("project").annotate(
            project_name=F("project__name"),
        )


class CategoryCreateView(AdminOrAccountantMixin, View):
    """Persist a new category name (AJAX from transaction form)."""

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            payload = {}
        name = normalize_category_name(payload.get("name") or request.POST.get("name"))
        if not name:
            return JsonResponse({"ok": False, "error": "Category name is required."}, status=400)
        ensure_category_exists(name)
        return JsonResponse({"ok": True, "name": name})


class TransactionCreateView(AdminOrAccountantMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/transaction_form.html"

    def get_success_url(self):
        return reverse_lazy("transactions:detail", kwargs={"pk": self.object.pk})


class TransactionUpdateView(AdminOrAccountantMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/transaction_form.html"

    def get_queryset(self):
        return Transaction.objects.select_related("project")

    def get_success_url(self):
        return reverse_lazy("transactions:detail", kwargs={"pk": self.object.pk})


class TransactionDeleteView(AdminOrAccountantMixin, DeleteView):
    model = Transaction
    template_name = "transactions/transaction_confirm_delete.html"
    success_url = reverse_lazy("transactions:list")


class LegacyPayableListView(AccountantOrAdminRequiredMixin, ListView):
    model = LegacyPayable
    template_name = "transactions/legacy_list.html"
    context_object_name = "legacy_rows"

    def get_queryset(self):
        return LegacyPayable.objects.annotate(
            remaining_calc=F("total_payable") - F("total_paid"),
        ).order_by("supplier_name", "pk")


class LegacyPayableCreateView(AdminOrAccountantMixin, CreateView):
    model = LegacyPayable
    form_class = LegacyPayableForm
    template_name = "transactions/legacy_form.html"
    success_url = reverse_lazy("transactions:legacy_list")


class LegacyPayableUpdateView(AdminOrAccountantMixin, UpdateView):
    model = LegacyPayable
    form_class = LegacyPayableForm
    template_name = "transactions/legacy_form.html"
    success_url = reverse_lazy("transactions:legacy_list")


class LegacyPayableDeleteView(AdminOrAccountantMixin, DeleteView):
    model = LegacyPayable
    template_name = "transactions/legacy_confirm_delete.html"
    success_url = reverse_lazy("transactions:legacy_list")
