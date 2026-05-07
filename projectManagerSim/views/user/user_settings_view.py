from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm
from projectManagerSim.forms import EmailChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.views.generic import View

from projectManagerSim.forms import EmailChangeForm


class UserSettingsView(LoginRequiredMixin, View):
    """
    Allows authenticated users to change their password and email
    """

    def post(self, request):
        if "change_password" in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            email_form = EmailChangeForm(user=request.user,instance=request.user)

            if password_form.is_valid():
                user = password_form.save()
                login(request, user)
                return redirect("user_settings")
            context = {"form": password_form,"email_form": email_form,}
            return render(request,"user_settings.html",context)
        if "change_email" in request.POST:
            email_form = EmailChangeForm(request.POST,user=request.user,instance=request.user)
            password_form = PasswordChangeForm(user=request.user)


            if email_form.is_valid():
                email_form.save()
                return redirect("user_settings")

            context = {"form": password_form,"email_form": email_form}
            return render(request,"user_settings.html",context)

    def get(self, request): 
        context = {"form": PasswordChangeForm(user=request.user),
               "email_form": EmailChangeForm(user=request.user, instance=request.user),
               "tour_step": request.session.pop('tour_step', ''),
        }
        return render(request,"user_settings.html",context)