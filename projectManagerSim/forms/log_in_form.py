from django import forms
from django.contrib.auth import authenticate

class LogInForm(forms.Form):
    """
        Form enabling registered users to log in and attempts
        to authenticate the user against Django’s authentication backend.

     """

    username = forms.CharField(help_text="Enter your username", label="Username")
    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text="Enter your password",
        label="Password"
    )

    def get_user(self):
        user = None
        if self.is_valid():
            username = self.cleaned_data.get("username") # used .get bc if username is empty it'll just return none
            password = self.cleaned_data.get("password")
            user = authenticate(username=username, password=password) #check the database & return user
        return user