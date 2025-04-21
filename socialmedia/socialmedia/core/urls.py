from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.sites.shortcuts import get_current_site
from .views import EmailTestView
from django.conf import settings

urlpatterns = [
    # Authentication URLs
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('landing/', views.landing, name='landing'),
    path('for_you/', views.for_you, name='for_you'),
    path('videocall/',views.videocall, name='videocall'),
    path('create_post/', views.create_post, name='create_post'),
    
    # Profile URLs
    path('profile/<str:username>/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    
    # Post URLs
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    
    # Friend URLs
    path('friends/', views.friends, name='friends'),
    path('friend-request/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('friend-request/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend-request/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('friend-request/cancel/<int:request_id>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('remove-friend/<str:username>/', views.remove_friend, name='remove_friend'),
    
    # Search URL
    path('search/', views.search, name='search'),
    
    # Password Reset URLs
    path('password-reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='core/password_reset.html',
            email_template_name='core/password_reset_email.html',
            subject_template_name='core/password_reset_subject.txt',
            success_url='done/',
            extra_context={'site': get_current_site}
        ),
        name='password_reset'),
    
    path('password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='core/password_reset_done.html'
        ),
        name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='core/password_reset_confirm.html',
            success_url='/password-reset-complete/'
        ),
        name='password_reset_confirm'),
    
    path('password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='core/password_reset_complete.html'
        ),
        name='password_reset_complete'),
    
    path('test-email/', EmailTestView.as_view(), name='test_email'),
    
   # Group URLs
    path('groups/', views.groups, name='groups'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),
    path('group/<int:group_id>/chat/', views.group_chat, name='group_chat'),
    # path('group/<int:group_id>/send-message/', views.send_group_message, name='send_group_message'),
    # path('group/<int:group_id>/start-call/', views.start_group_call, name='start_group_call'),
    # path('call/<int:call_id>/end/', views.end_group_call, name='end_group_call'),
    # path('call/<int:call_id>/join/', views.join_group_call, name='join_group_call'),
    # path('group-post/<int:post_id>/like/', views.like_group_post, name='like_group_post'),
     path('groups/<int:group_id>/edit/', views.group_edit, name='group_edit'),
    path('groups/<int:group_id>/delete/', views.group_delete, name='group_delete'),  # Ensure group_delete is also defined
]
