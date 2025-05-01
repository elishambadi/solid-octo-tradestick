# forex_journal/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('trading_journal.urls')),
]

# Add media URL patterns in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# trading_journal/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomLoginForm

urlpatterns = [
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='trading_journal/login.html',
        authentication_form=CustomLoginForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Main dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    
    # Journal entries
    path('journal/', views.journal_entry_list, name='journal_entry_list'),
    path('journal/new/', views.journal_entry_create, name='journal_entry_create'),
    path('journal/<int:pk>/edit/', views.journal_entry_edit, name='journal_entry_edit'),
    path('journal/<int:pk>/delete/', views.journal_entry_delete, name='journal_entry_delete'),
    
    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/new/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    
    # Analysis
    path('performance/', views.performance_analysis, name='performance_analysis'),
    path('mood-analysis/', views.mood_analysis, name='mood_analysis'),
    
    # Mood management
    path('moods/', views.manage_moods, name='manage_moods'),
]