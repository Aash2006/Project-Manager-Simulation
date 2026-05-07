from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
#
class SignUpForm(UserCreationForm):

    email = forms.EmailField(required=True, label="Email Address")

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})