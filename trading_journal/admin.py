# trading_journal/admin.py

from django.contrib import admin
from .models import TraderProfile, JournalEntry, Transaction, MoodChoice

@admin.register(TraderProfile)
class TraderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tradingview_account', 'starting_balance', 'current_balance', 'date_created')
    search_fields = ('user__username', 'user__email', 'tradingview_account')
    list_filter = ('date_created',)

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('trader', 'date', 'daily_pnl', 'mood', 'created_at')
    list_filter = ('date', 'mood')
    search_fields = ('trader__user__username', 'notes')
    date_hierarchy = 'date'

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('trader', 'transaction_type', 'amount', 'date', 'created_at')
    list_filter = ('transaction_type', 'date')
    search_fields = ('trader__user__username', 'description')
    date_hierarchy = 'date'

@admin.register(MoodChoice)
class MoodChoiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)