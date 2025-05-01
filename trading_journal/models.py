# trading_journal/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from colorfield.fields import ColorField
from ckeditor.fields import RichTextField
from django.utils import timezone

class MoodChoice(models.Model):
    name = models.CharField(max_length=50)
    color = ColorField(default='#FF0000')
    
    def __str__(self):
        return self.name

class TraderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trader_profile')
    tradingview_account = models.CharField(max_length=100, blank=True, null=True)
    starting_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def update_balance(self):
        """Update the current balance based on journal entries and transactions"""
        # Start with the initial balance
        balance = self.starting_balance
        
        # Add all deposits and subtract all withdrawals
        transactions = Transaction.objects.filter(trader=self)
        for transaction in transactions:
            if transaction.transaction_type == 'DEPOSIT':
                balance += transaction.amount
            else:
                balance -= transaction.amount
        
        # Add all PnL from journal entries
        journal_entries = JournalEntry.objects.filter(trader=self)
        for entry in journal_entries:
            balance += entry.daily_pnl
        
        # Update the current balance
        self.current_balance = balance
        self.save()

class JournalEntry(models.Model):
    trader = models.ForeignKey(TraderProfile, on_delete=models.CASCADE, related_name='journal_entries')
    date = models.DateField(default=timezone.now)
    daily_pnl = models.DecimalField(max_digits=15, decimal_places=2)
    mood = models.ForeignKey(MoodChoice, on_delete=models.SET_NULL, null=True, blank=True)
    notes = RichTextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Journal Entries"
        unique_together = ['trader', 'date']  # Only one entry per day per trader
    
    def __str__(self):
        return f"{self.trader.user.username}'s Entry on {self.date}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the trader's balance whenever an entry is saved
        self.trader.update_balance()

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
    ]
    
    trader = models.ForeignKey(TraderProfile, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.transaction_type} of {self.amount} on {self.date}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the trader's balance whenever a transaction is saved
        self.trader.update_balance()

# Signal to create a TraderProfile when a new User is created
@receiver(post_save, sender=User)
def create_trader_profile(sender, instance, created, **kwargs):
    if created:
        TraderProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_trader_profile(sender, instance, **kwargs):
    instance.trader_profile.save()