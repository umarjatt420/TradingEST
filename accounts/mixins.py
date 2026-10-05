from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url

from .models import Role


class SessionAuthenticatedMixin:
    """Session-based auth check — not Django's LoginRequiredMixin."""

    login_url = None
    redirect_field_name = REDIRECT_FIELD_NAME

    def get_login_url(self):
        return self.login_url or settings.LOGIN_URL

    def resolve_redirect(self, request):
        resolved = resolve_url(self.get_login_url())
        if self.redirect_field_name:
            next_url = request.get_full_path()
            sep = "&" if "?" in resolved else "?"
            return f"{resolved}{sep}{urlencode({self.redirect_field_name: next_url})}"
        return resolved

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(self.resolve_redirect(request))
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin(SessionAuthenticatedMixin):
    """Must be authenticated and have one of `allowed_roles`."""

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(self.resolve_redirect(request))
        role = getattr(request.user, "role", None)
        if role not in self.allowed_roles:
            raise PermissionDenied("Insufficient role.")
        # Skip duplicate SessionAuthenticatedMixin check in MRO
        return super(SessionAuthenticatedMixin, self).dispatch(request, *args, **kwargs)


class AccountantOrAdminRequiredMixin(RoleRequiredMixin):
    """
    Financial / HR / legacy reports — not exposed to Viewer.
    Use for views that should only be reachable by Accountant or Admin (same URLs enforced server-side).
    """

    allowed_roles = (Role.ACCOUNTANT, Role.ADMIN)


class AdminOnlyMixin(SessionAuthenticatedMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(self.resolve_redirect(request))
        if getattr(request.user, "role", None) != Role.ADMIN:
            raise PermissionDenied("Admin only.")
        return super(SessionAuthenticatedMixin, self).dispatch(request, *args, **kwargs)


class AdminOrAccountantMixin(SessionAuthenticatedMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(self.resolve_redirect(request))
        if getattr(request.user, "role", None) not in (Role.ADMIN, Role.ACCOUNTANT):
            raise PermissionDenied("Edit permission required.")
        return super(SessionAuthenticatedMixin, self).dispatch(request, *args, **kwargs)


class ViewerReadOnlyMixin(SessionAuthenticatedMixin):
    """Viewer may GET; mutations require Admin or Accountant."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(self.resolve_redirect(request))
        role = getattr(request.user, "role", None)
        if role == Role.VIEWER and request.method not in ("GET", "HEAD", "OPTIONS"):
            raise PermissionDenied("Read-only users cannot modify data.")
        return super(SessionAuthenticatedMixin, self).dispatch(request, *args, **kwargs)
