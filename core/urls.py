from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    # 🛡️ Disclaimer page route
    path('disclaimer/', views.disclaimer, name='disclaimer'),

    # 🧩 Authentication
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),

    # 🏠 Home
    path('', views.home, name='home'),

    # 📖 Stories Section
    path('stories/', views.stories, name='stories'),  # list of all stories
    path('story/create/', views.create_story, name='create_story'),
    path('story/<int:story_id>/', views.story_detail, name='story_detail'),
    path('story/<int:story_id>/react/<str:reaction_type>/', views.react_to_story, name='react_to_story'),
    path('react_to_story/<int:story_id>/<str:reaction_type>/', views.react_to_story, name='react_to_story'),

    # User Profile
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # User's Own Stories
    path('my-stories/', views.my_stories, name='my_stories'),
    path('story/<int:story_id>/edit/', views.edit_story, name='edit_story'),
    path('story/delete/<int:story_id>/', views.delete_story, name='delete_story'),

    # 🤖 AI Chatbot
    path('chat/', views.chat_page, name='chat_page'),
    path('chat/ask/', views.ask_ai, name='ask_ai'),

    # 🚨 Distress Alerts
    path("alerts/", views.distress_alerts, name="distress_alerts"),
    path("delete-alert/<int:alert_id>/", views.delete_alert, name="delete_alert"),

    # 📝 Journals Section
    path('journals/', views.journals, name='journals'),
    path('journal/create/', views.create_journal, name='create_journal'),
    path('journal/<int:journal_id>/', views.journal_detail, name='journal_detail'),
    path('journal/<int:journal_id>/edit/', views.edit_journal, name='edit_journal'),
    path('journal/<int:journal_id>/delete/', views.delete_journal, name='delete_journal'),
]
