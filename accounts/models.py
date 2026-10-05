from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    ACCOUNTANT = "accountant", "Accountant"
    VIEWER = "viewer", "Viewer"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        """Name shown in the header (full name, or email local-part)."""
        name = (self.full_name or "").strip()
        if name:
            return name
        return self.email.split("@")[0] if self.email else ""

    def save(self, *args, **kwargs):
        self.is_staff = self.role == Role.ADMIN
        super().save(*args, **kwargs)
