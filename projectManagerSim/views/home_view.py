from django.shortcuts import redirect
from django.views import View


class HomeView(View):
    def get(self, request):
        # Not logged in
        if not request.user.is_authenticated:
            return redirect('log_in')
        # Admin users
        elif request.user.is_staff:
            return redirect('admin_dashboard')
        # Regular authenticated users
        else:
            return redirect('user_dashboard')