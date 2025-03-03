from django import forms
from django.contrib.auth.hashers import make_password #greate
from django.contrib.auth.models import User #greate
from .models import Budget, Transaction

#here this sign up form is created from the User model
class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)  # Ensure password input is hidden
    class Meta:
        model=User
        fields=['username','email','password']
        
    #love it.It hashes the password
    def save(self, commit=True):
        user= super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # Hash the password  # Hash the password
        if commit:
            user.save()
        return user



class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'p-2 border rounded', 'placeholder': 'Enter budget'}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['description', 'amount', 'type','category']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'p-2 border rounded', 'placeholder': 'Description'}),
            'amount': forms.NumberInput(attrs={'class': 'p-2 border rounded', 'placeholder': 'Amount'}),
            'type': forms.Select(attrs={'class': 'p-2 border rounded'}),
            'category':forms.Select(attrs={'class': 'p-2 border rounded'}),
        }
