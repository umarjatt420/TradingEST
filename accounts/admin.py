from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "role", "is_staff", "is_active", "date_joined")
    search_fields = ("email", "full_name")
    list_filter = ("role", "is_active")
    readonly_fields = ("date_joined", "last_login")
