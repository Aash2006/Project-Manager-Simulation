from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View

from projectManagerSim.forms.log_in_form import LogInForm


class LogInView(View):
    def get(self, request):
        form = LogInForm()
        # If the user has not logged in yet
        if not request.user.is_authenticated:
            return render(request, 'log_in.html', {'form': form})
        else:
            return redirect('home')
        
    def post(self, request):
        form = LogInForm(request.POST)

        if form.is_valid():
            user = form.get_user()

            if user is not None:
                login(request, user)

                if not request.session.get('tour_step') and not request.session.get('tour_complete'):
                    request.session['tour_step'] = 'dashboard'

                if user.is_staff:
                    return redirect('admin_dashboard')
                else:
                    return redirect('user_dashboard')

            else:
                messages.error(request, "User does not exist!")
                return render(request, 'log_in.html', {'form': form})
        else:
            messages.error(request, "Invalid form!")
            return render(request, 'log_in.html', {'form': form})
            
    