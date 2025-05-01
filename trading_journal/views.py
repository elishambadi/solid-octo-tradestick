# trading_journal/views.py

import json
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from django.utils import timezone
from .models import TraderProfile, JournalEntry, Transaction, MoodChoice
from .forms import (CustomUserCreationForm, JournalEntryForm, TransactionForm, 
                   MoodChoiceForm, ProfileUpdateForm, UserUpdateForm)

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Your account has been created! You are now logged in.')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'trading_journal/register.html', {'form': form})

@login_required
def dashboard(request):
    """Main dashboard view showing summary and recent activity"""
    trader = request.user.trader_profile
    
    # Get recent journal entries
    recent_entries = JournalEntry.objects.filter(trader=trader).order_by('-date')[:5]
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(trader=trader).order_by('-date')[:5]
    
    # Calculate performance metrics
    total_pnl = JournalEntry.objects.filter(trader=trader).aggregate(Sum('daily_pnl'))['daily_pnl__sum'] or 0
    
    # Generate performance chart
    performance_chart = generate_performance_chart(trader)
    
    # Mood distribution
    mood_data = generate_mood_distribution(trader)
    
    context = {
        'trader': trader,
        'recent_entries': recent_entries,
        'recent_transactions': recent_transactions,
        'total_pnl': total_pnl,
        'performance_chart': performance_chart,
        'mood_data': mood_data,
    }
    
    return render(request, 'trading_journal/dashboard.html', context)

@login_required
def journal_entry_list(request):
    """View all journal entries"""
    trader = request.user.trader_profile
    entries = JournalEntry.objects.filter(trader=trader).order_by('-date')
    
    return render(request, 'trading_journal/journal_entry_list.html', {
        'entries': entries
    })

@login_required
def journal_entry_create(request):
    """Create a new journal entry"""
    trader = request.user.trader_profile
    
    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.trader = trader
            
            # Check for duplicate entry for same date
            existing_entry = JournalEntry.objects.filter(trader=trader, date=entry.date).first()
            if existing_entry:
                messages.error(request, f'An entry for {entry.date} already exists.')
                return render(request, 'trading_journal/journal_entry_form.html', {'form': form})
                
            entry.save()
            messages.success(request, 'Journal entry added successfully!')
            return redirect('journal_entry_list')
    else:
        # Pre-fill with today's date
        form = JournalEntryForm(initial={'date': timezone.now().date()})
    
    return render(request, 'trading_journal/journal_entry_form.html', {
        'form': form,
        'title': 'Add New Journal Entry'
    })

@login_required
def journal_entry_edit(request, pk):
    """Edit an existing journal entry"""
    trader = request.user.trader_profile
    entry = get_object_or_404(JournalEntry, pk=pk, trader=trader)
    
    if request.method == 'POST':
        form = JournalEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Journal entry updated successfully!')
            return redirect('journal_entry_list')
    else:
        form = JournalEntryForm(instance=entry)
    
    return render(request, 'trading_journal/journal_entry_form.html', {
        'form': form,
        'title': 'Edit Journal Entry'
    })

@login_required
def journal_entry_delete(request, pk):
    """Delete a journal entry"""
    trader = request.user.trader_profile
    entry = get_object_or_404(JournalEntry, pk=pk, trader=trader)
    
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Journal entry deleted successfully!')
        return redirect('journal_entry_list')
    
    return render(request, 'trading_journal/journal_entry_confirm_delete.html', {
        'entry': entry
    })

@login_required
def transaction_list(request):
    """View all transactions"""
    trader = request.user.trader_profile
    transactions = Transaction.objects.filter(trader=trader).order_by('-date')
    
    return render(request, 'trading_journal/transaction_list.html', {
        'transactions': transactions
    })

@login_required
def transaction_create(request):
    """Create a new transaction (deposit/withdrawal)"""
    trader = request.user.trader_profile
    
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.trader = trader
            transaction.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('transaction_list')
    else:
        # Pre-fill with today's date
        form = TransactionForm(initial={'date': timezone.now().date()})
    
    return render(request, 'trading_journal/transaction_form.html', {
        'form': form,
        'title': 'Add New Transaction'
    })

@login_required
def transaction_edit(request, pk):
    """Edit an existing transaction"""
    trader = request.user.trader_profile
    transaction = get_object_or_404(Transaction, pk=pk, trader=trader)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully!')
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction)
    
    return render(request, 'trading_journal/transaction_form.html', {
        'form': form,
        'title': 'Edit Transaction'
    })

@login_required
def transaction_delete(request, pk):
    """Delete a transaction"""
    trader = request.user.trader_profile
    transaction = get_object_or_404(Transaction, pk=pk, trader=trader)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
        return redirect('transaction_list')
    
    return render(request, 'trading_journal/transaction_confirm_delete.html', {
        'transaction': transaction
    })

@login_required
def profile(request):
    """View and update user profile"""
    trader = request.user.trader_profile
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=trader)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=trader)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'trader': trader
    }
    
    return render(request, 'trading_journal/profile.html', context)

@login_required
def performance_analysis(request):
    """Advanced performance analytics view"""
    trader = request.user.trader_profile
    
    # Get all journal entries
    entries = JournalEntry.objects.filter(trader=trader).order_by('date')
    
    if not entries:
        messages.info(request, 'No journal entries found to analyze.')
        return redirect('dashboard')
    
    # Generate performance charts
    performance_chart = generate_performance_chart(trader)
    daily_pnl_chart = generate_daily_pnl_chart(trader)
    
    # Calculate performance metrics
    total_days = entries.count()
    profitable_days = entries.filter(daily_pnl__gt=0).count()
    win_rate = (profitable_days / total_days * 100) if total_days > 0 else 0
    
    total_pnl = entries.aggregate(Sum('daily_pnl'))['daily_pnl__sum'] or 0
    avg_daily_pnl = total_pnl / total_days if total_days > 0 else 0
    
    # Find best and worst days
    best_day = entries.order_by('-daily_pnl').first()
    worst_day = entries.order_by('daily_pnl').first()
    
    context = {
        'performance_chart': performance_chart,
        'daily_pnl_chart': daily_pnl_chart,
        'total_days': total_days,
        'profitable_days': profitable_days,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_daily_pnl': avg_daily_pnl,
        'best_day': best_day,
        'worst_day': worst_day,
    }
    
    return render(request, 'trading_journal/performance_analysis.html', context)

@login_required
def mood_analysis(request):
    """Analyze trading performance by mood"""
    trader = request.user.trader_profile
    
    # Get all mood choices
    moods = MoodChoice.objects.all()
    
    # Initialize data structure for analysis
    mood_data = []
    
    for mood in moods:
        entries = JournalEntry.objects.filter(trader=trader, mood=mood)
        total_entries = entries.count()
        
        if total_entries > 0:
            total_pnl = entries.aggregate(Sum('daily_pnl'))['daily_pnl__sum'] or 0
            avg_pnl = total_pnl / total_entries
            profitable_days = entries.filter(daily_pnl__gt=0).count()
            win_rate = (profitable_days / total_entries * 100) if total_entries > 0 else 0
            
            mood_data.append({
                'mood': mood.name,
                'color': mood.color,
                'count': total_entries,
                'total_pnl': total_pnl,
                'avg_pnl': avg_pnl,
                'win_rate': win_rate
            })
    
    # Generate mood distribution chart
    mood_chart = generate_mood_chart(trader)
    
    return render(request, 'trading_journal/mood_analysis.html', {
        'mood_data': mood_data,
        'mood_chart': mood_chart
    })

@login_required
def manage_moods(request):
    """Create and manage mood choices"""
    if request.method == 'POST':
        form = MoodChoiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'New mood added successfully!')
            return redirect('manage_moods')
    else:
        form = MoodChoiceForm()
    
    moods = MoodChoice.objects.all()
    
    return render(request, 'trading_journal/manage_moods.html', {
        'form': form,
        'moods': moods
    })

# --- Helper functions for chart generation ---

def generate_performance_chart(trader):
    """Generate cumulative performance chart"""
    # Get journal entries and transactions
    entries = JournalEntry.objects.filter(trader=trader).order_by('date')
    transactions = Transaction.objects.filter(trader=trader).order_by('date')
    
    if not entries and not transactions:
        return None
    
    # Create DataFrame for journal entries
    df_entries = pd.DataFrame(list(entries.values('date', 'daily_pnl')))
    
    # Create DataFrame for transactions
    if transactions:
        df_transactions = pd.DataFrame(list(transactions.values('date', 'transaction_type', 'amount')))
        # Convert withdrawal amounts to negative
        df_transactions['amount'] = df_transactions.apply(
            lambda row: -row['amount'] if row['transaction_type'] == 'WITHDRAWAL' else row['amount'], 
            axis=1
        )
    else:
        df_transactions = pd.DataFrame(columns=['date', 'amount'])
    
    # Combine data
    all_dates = pd.concat([
        df_entries[['date']].rename(columns={'date': 'date'}),
        df_transactions[['date']].rename(columns={'date': 'date'})
    ]).drop_duplicates().sort_values('date')
    
    # Create complete timeline DataFrame
    timeline = pd.DataFrame({'date': all_dates['date']})
    
    # Add PnL and transaction amounts
    if not df_entries.empty:
        timeline = timeline.merge(
            df_entries.groupby('date')['daily_pnl'].sum().reset_index(),
            on='date', how='left'
        )
    else:
        timeline['daily_pnl'] = 0
    
    if not df_transactions.empty:
        timeline = timeline.merge(
            df_transactions.groupby('date')['amount'].sum().reset_index(),
            on='date', how='left'
        )
    else:
        timeline['amount'] = 0
    
    # Replace NaN with 0
    timeline.fillna(0, inplace=True)
    
    # Calculate cumulative sum
    timeline['cumulative_pnl'] = timeline['daily_pnl'].cumsum()
    timeline['cumulative_transactions'] = timeline['amount'].cumsum()
    timeline['balance'] = trader.starting_balance + timeline['cumulative_pnl'] + timeline['cumulative_transactions']
    
    # Generate chart
    plt.figure(figsize=(10, 6))
    plt.plot(timeline['date'], timeline['balance'], marker='o', linestyle='-', color='#1E90FF')
    plt.title('Account Balance Over Time', fontsize=14)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Balance', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Set y-axis to start from a round number below the minimum balance
    min_balance = timeline['balance'].min()
    plt.ylim(bottom=max(0, (min_balance//100)*100))
    
    # Format the plot for forex trading style
    plt.tight_layout()
    
    # Save plot to a bytes buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    
    # Convert to base64 for HTML display
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{image_base64}'

def generate_daily_pnl_chart(trader):
    """Generate bar chart showing daily PnL"""
    entries = JournalEntry.objects.filter(trader=trader).order_by('date')
    
    if not entries:
        return None
    
    # Create DataFrame
    df = pd.DataFrame(list(entries.values('date', 'daily_pnl')))
    
    # Generate chart
    plt.figure(figsize=(10, 6))
    
    # Set colors based on profit/loss
    colors = ['#4CAF50' if pnl >= 0 else '#F44336' for pnl in df['daily_pnl']]
    
    plt.bar(df['date'], df['daily_pnl'], color=colors)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    plt.title('Daily Profit/Loss', fontsize=14)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('PnL', fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Format the plot for forex trading style
    plt.tight_layout()
    
    # Save plot to a bytes buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    
    # Convert to base64 for HTML display
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{image_base64}'

def generate_mood_chart(trader):
    """Generate chart showing performance by mood"""
    entries = JournalEntry.objects.filter(trader=trader).exclude(mood=None)
    
    if not entries:
        return None
    
    # Group by mood and calculate metrics
    mood_metrics = []
    
    for mood in MoodChoice.objects.all():
        mood_entries = entries.filter(mood=mood)
        count = mood_entries.count()
        
        if count > 0:
            avg_pnl = mood_entries.aggregate(Sum('daily_pnl'))['daily_pnl__sum'] / count
            mood_metrics.append({
                'mood': mood.name,
                'color': mood.color,
                'avg_pnl': avg_pnl,
                'count': count
            })
    
    if not mood_metrics:
        return None
    
    # Create DataFrame
    df = pd.DataFrame(mood_metrics)
    
    # Generate chart
    plt.figure(figsize=(10, 6))
    
    bars = plt.bar(df['mood'], df['avg_pnl'], color=df['color'])
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    plt.title('Average PnL by Mood', fontsize=14)
    plt.xlabel('Mood', fontsize=12)
    plt.ylabel('Average PnL', fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add count labels
    for bar, count in zip(bars, df['count']):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'n={count}', ha='center', va='bottom')
    
    # Format the plot for forex trading style
    plt.tight_layout()
    
    # Save plot to a bytes buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    
    # Convert to base64 for HTML display
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{image_base64}'

def generate_mood_distribution(trader):
    """Generate data for mood distribution"""
    entries = JournalEntry.objects.filter(trader=trader).exclude(mood=None)
    
    if not entries:
        return None
    
    # Count entries by mood
    mood_counts = {}
    for mood in MoodChoice.objects.all():
        count = entries.filter(mood=mood).count()
        if count > 0:
            mood_counts[mood.name] = {
                'count': count,
                'color': mood.color
            }
    
    return mood_counts