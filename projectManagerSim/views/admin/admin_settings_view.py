from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import View

from projectManagerSim.forms import EmailChangeForm


@method_decorator(staff_member_required, name="dispatch")
class AdminSettingsView(View):
    template_name = "admin/admin_settings.html"

    def _context(self, request, password_form=None, email_form=None):
        return {
            "form": password_form or PasswordChangeForm(user=request.user),
            "email_form": email_form or EmailChangeForm(user=request.user, instance=request.user),
        }

    def get(self, request):
        return render(request, self.template_name, self._context(request))

    def post(self, request):
        if "change_password" in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                login(request, user)
                return redirect("admin_settings")
            return render(request, self.template_name, self._context(request, password_form=password_form))

        if "change_email" in request.POST:
            email_form = EmailChangeForm(request.POST, user=request.user, instance=request.user)
            if email_form.is_valid():
                email_form.save()
                return redirect("admin_settings")
            return render(request, self.template_name, self._context(request, email_form=email_form))
