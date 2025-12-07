from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ClearableFileInput
from .models import CustomUser, Article

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "role")

class ArticleForm(forms.ModelForm):

    images = forms.FileField(
        widget=ClearableFileInput(),  # без multiple, як ти просив
        required=False
    )

    videos = forms.FileField(
        widget=ClearableFileInput(),
        required=False
    )

    class Meta:
        model = Article
        fields = ["title", "content", "category", "tags", "status"]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Назва статті"
            }),

            "content": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Введіть текст статті..."
            }),

            "category": forms.Select(attrs={
                "class": "form-control"
            }),

            "tags": forms.CheckboxSelectMultiple(
                attrs={"class": "form-check"}
            ),

            "status": forms.RadioSelect(
                attrs={"class": "form-check-input"}
            ),
        }

 