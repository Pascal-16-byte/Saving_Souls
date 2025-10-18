from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('manage-stories/', views.all_stories, name='all_stories'),

    # 🧩 Authentication
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),

    # 🏠 Home
    path('', views.home, name='home'),

    # 📖 Stories Section
    path('stories/', views.stories, name='stories'),  # list of all stories
    path('stories/new/', views.create_post, name='create_post'),  # create a new story
    path('stories/<int:post_id>/', views.post_detail, name='post_detail'),  # view single story

    # 💬 Reactions
    path('stories/<int:post_id>/react/<str:reaction_type>/', views.react_to_post, name='react_to_post'),

    # User Profile
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # User's Own Stories
    path('my-stories/', views.my_stories, name='my_stories'),
    path('story/edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('story/delete/<int:post_id>/', views.delete_post, name='delete_post'),

    # 🤖 AI Chatbot
    path('chat/', views.chat_page, name='chat_page'),
    path('chat/ask/', views.ask_ai, name='ask_ai'),

    # 🚨 Distress Alerts
    path("alerts/", views.distress_alerts, name="distress_alerts"),
    path("delete-alert/<int:alert_id>/", views.delete_alert, name="delete_alert"),
]
