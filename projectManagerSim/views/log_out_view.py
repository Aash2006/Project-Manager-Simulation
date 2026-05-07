from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def log_out(request):
    """Log out the current user"""
    logout(request)
    return redirect('home')
