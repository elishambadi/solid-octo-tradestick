# trading_journal/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import TraderProfile, JournalEntry, Transaction, MoodChoice
from ckeditor.widgets import CKEditorWidget

class CustomUserCreationForm(UserCreationForm):
    """Extended user registration form with trader profile fields"""
    email = forms.EmailField(required=True)
    tradingview_account = forms.CharField(max_length=100, required=False)
    starting_balance = forms.DecimalField(max_digits=15, decimal_places=2, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Update the trader profile with additional information
            profile = user.trader_profile
            profile.tradingview_account = self.cleaned_data.get('tradingview_account', '')
            profile.starting_balance = self.cleaned_data.get('starting_balance', 0)
            profile.current_balance = profile.starting_balance  # Initialize current balance
            profile.save()
        
        return user

class CustomLoginForm(AuthenticationForm):
    """Custom login form with additional styling"""
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class JournalEntryForm(forms.ModelForm):
    """Form for creating and editing journal entries"""
    notes = forms.CharField(widget=CKEditorWidget(), required=False)
    
    class Meta:
        model = JournalEntry
        fields = ['date', 'daily_pnl', 'mood', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'daily_pnl': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class TransactionForm(forms.ModelForm):
    """Form for creating deposit/withdrawal transactions"""
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'description', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
        }

class MoodChoiceForm(forms.ModelForm):
    """Form for creating custom mood choices"""
    class Meta:
        model = MoodChoice
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating trader profile"""
    class Meta:
        model = TraderProfile
        fields = ['tradingview_account']
        widgets = {
            'tradingview_account': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UserUpdateForm(forms.ModelForm):
    """Form for updating user information"""
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }