from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import View


class UserDashboardView(LoginRequiredMixin, View):
    """Simple user dashboard view that shows Play and Settings."""

    def get(self, request):
        context = {}
        return render(request, "user_dashboard.html", context)