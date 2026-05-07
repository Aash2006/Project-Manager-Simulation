from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailChangeForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Current password"
    )
    email = forms.EmailField(
        required=True,
        max_length=254
    )
    class Meta:
        model = User
        fields = ["email"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password.")
        return password

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email