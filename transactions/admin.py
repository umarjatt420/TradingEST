from django.contrib import admin

from .models import LegacyPayable, Transaction, TransactionCategory


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "reference_number",
        "date",
        "flow_type",
        "amount_excl_vat",
        "total_amount",
        "account",
        "category",
        "project",
    )
    list_filter = ("flow_type", "account", "date")
    search_fields = ("reference_number", "description", "party_name", "notes")
    raw_id_fields = ("project",)
    date_hierarchy = "date"


@admin.register(LegacyPayable)
class LegacyPayableAdmin(admin.ModelAdmin):
    list_display = ("supplier_name", "total_payable", "total_paid", "projects_name")
