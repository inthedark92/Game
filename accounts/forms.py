from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

class LoginForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=150,
                               widget=forms.TextInput(attrs={'placeholder': 'Введите логин'}))
    password = forms.CharField(label='Пароль',
                               widget=forms.PasswordInput(attrs={'placeholder': 'Введите пароль'}))

class RegisterForm(UserCreationForm):
    username = forms.CharField(label='Логин', max_length=150,
                               widget=forms.TextInput(attrs={'placeholder': 'Введите логин'}))
    password1 = forms.CharField(label='Пароль',
                                widget=forms.PasswordInput(attrs={'placeholder': 'Введите пароль'}))
    password2 = forms.CharField(label='Повторите пароль',
                                widget=forms.PasswordInput(attrs={'placeholder': 'Повторите пароль'}))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('Пользователь с таким логином уже существует')
        return username
    
    
