from projectManagerSim.forms.sign_up_form import SignUpForm
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View


class SignUpView(View):
    def get(self, request):
        form = SignUpForm()
        return render(request, 'sign_up.html', {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            login(request, user)
            request.session['tour_step'] = 'prompt'
            return redirect('user_dashboard')
        else:
            return render(request, 'sign_up.html', {'form': form})