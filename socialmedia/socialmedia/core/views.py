from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.contrib import messages
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.views import View
from django.core.mail import send_mail
from django.conf import settings
import json
from datetime import timedelta
from django.contrib.auth.tokens import default_token_generator
import logging

from .forms import (
    CustomUserCreationForm, 
    PostForm, 
    CommentForm, 
    CustomUserChangeForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    GroupForm,
    GroupPostForm,
    GroupMessageForm,
    GroupCallForm   
)
from .models import (
    Post, 
    Comment, 
    User, 
    FriendRequest, 
    Group, 
    GroupPost, 
    GroupMessage,
    GroupCall,
    Notification
)


logger = logging.getLogger(__name__)

# ======================
# Authentication Views
# ======================

def home(request):
    if request.user.is_authenticated:
        try:
            friends = request.user.friends.all()
            posts = Post.objects.filter(
                Q(user=request.user) | 
                Q(user__in=friends)
            ).order_by('-created_at')
        except AttributeError:
            posts = Post.objects.filter(user=request.user).order_by('-created_at')
            messages.warning(request, "Friends feature not properly configured")
        
        form = PostForm()
        
        if request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                post = form.save(commit=False)
                post.user = request.user
                
                if post.media_file:
                    file_extension = post.media_file.name.split('.')[-1].lower()
                    if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
                        post.media_type = 'image'
                    elif file_extension in ['mp4', 'webm', 'ogg']:
                        post.media_type = 'video'
                    elif file_extension in ['mp3', 'wav']:
                        post.media_type = 'audio'
                
                post.save()
                messages.success(request, 'Post created successfully!')
                return redirect('home')
        
        context = {'posts': posts, 'form': form}
        return render(request, 'core/home.html', context)
    return render(request, 'core/landing.html')
def landing(request):
    return render(request, 'core/landing.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            
            # Redirect superusers to the Django admin site
            if user.is_superuser:
                return redirect('/admin/')
            
            return redirect('home')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'core/login.html')
    

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('home')

# ======================
# Profile Views
# ======================

@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=user).order_by('-created_at')
    is_self = request.user == user
    is_friend = request.user in user.friends.all()
    
    friend_request = None
    if not is_self and not is_friend:
        friend_request = FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=user) | 
            Q(from_user=user, to_user=request.user)
        ).first()
    
    context = {
        'profile_user': user,
        'posts': posts,
        'is_self': is_self,
        'is_friend': is_friend,
        'friend_request': friend_request,
    }
    return render(request, 'core/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile', username=request.user.username)
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'core/edit_profile.html', {'form': form})

# ======================
# Post Views
# ======================

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post).order_by('created_at')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            messages.success(request, 'Comment added!')
            return redirect('post_detail', post_id=post.id)
    else:
        form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'core/post_detail.html', context)

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()
    messages.success(request, 'Post deleted successfully!')
    return redirect('home')

# ======================
# Friend Views
# ======================

@login_required
def friends(request):
    user = request.user
    friends = user.friends.all()
    incoming_requests = FriendRequest.objects.filter(to_user=user, accepted=False)
    outgoing_requests = FriendRequest.objects.filter(from_user=user, accepted=False)
    
    context = {
        'friends': friends,
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
    }
    return render(request, 'core/friends.html', context)

@login_required
def send_friend_request(request, username):
    to_user = get_object_or_404(User, username=username)
    
    if FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
        messages.warning(request, 'Friend request already sent!')
    elif FriendRequest.objects.filter(from_user=to_user, to_user=request.user).exists():
        messages.warning(request, 'This user has already sent you a friend request!')
    else:
        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        messages.success(request, 'Friend request sent!')
    
    return redirect('profile', username=username)

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.accepted = True
    friend_request.save()
    
    request.user.friends.add(friend_request.from_user)
    friend_request.from_user.friends.add(request.user)
    
    messages.success(request, f'You are now friends with {friend_request.from_user.username}!')
    return redirect('friends')

@login_required
def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.delete()
    messages.success(request, 'Friend request rejected.')
    return redirect('friends')

@login_required
def cancel_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, from_user=request.user)
    friend_request.delete()
    messages.success(request, 'Friend request canceled.')
    return redirect('friends')

@login_required
def remove_friend(request, username):
    friend = get_object_or_404(User, username=username)
    request.user.friends.remove(friend)
    friend.friends.remove(request.user)
    
    FriendRequest.objects.filter(
        Q(from_user=request.user, to_user=friend) | 
        Q(from_user=friend, to_user=request.user)
    ).delete()
    
    messages.success(request, f'{friend.username} removed from your friends list.')
    return redirect('friends')

# ======================
# Search View
# ======================

@login_required
def search(request):
    query = request.GET.get('q', '')
    users = []
    
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(bio__icontains=query)
        ).exclude(id=request.user.id)
        
        for user in users:
            user.is_friend = user in request.user.friends.all()
            user.pending_request = FriendRequest.objects.filter(
                from_user=request.user,
                to_user=user
            ).exists()
    
    context = {'users': users, 'query': query}
    return render(request, 'core/search.html', context)

# ======================
# Password Reset Views
# ======================



from django.contrib.sites.shortcuts import get_current_site

class CustomPasswordResetView(PasswordResetView):
    template_name = 'core/password_reset.html'
    email_template_name = 'core/password_reset_email.html'
    subject_template_name = 'core/password_reset_subject.txt'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('password_reset_done')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_site = get_current_site(self.request)
        context.update({
            'domain': current_site.domain,  # Dynamically set the domain
            'protocol': 'https' if self.request.is_secure() else 'http',  # Use HTTPS if secure
        })
        return context

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': default_token_generator,
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': None,
            'extra_email_context': self.get_context_data(),
        }
        form.save(**opts)
        return super().form_valid(form)


@login_required
def groups(request):
    # Fetch recommended groups (public groups the user hasn't joined)
    recommended_groups = Group.objects.filter(privacy='public').exclude(members=request.user).order_by('?')[:4]
    
    # Fetch groups the user has joined
    user_groups = Group.objects.filter(members=request.user)

    # Handle group creation
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            group.members.add(request.user)  # Add the creator as a member
            messages.success(request, 'Group created successfully!')
            return redirect('group_detail', group_id=group.id)  # Redirect to the group detail page
    else:
        form = GroupForm()

    # Pass the context to the template
    context = {
        'recommended_groups': recommended_groups,
        'user_groups': user_groups,
        'form': form,
    }
    return render(request, 'core/groups.html', context)
    recommended_groups = Group.objects.filter(privacy='public').exclude(members=request.user).order_by('?')[:4]
    user_groups = request.user.joined_groups.all()
    
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            group.members.add(request.user)
            messages.success(request, 'Group created successfully!')
            return redirect('group_detail', group_id=group.id)
    else:
        form = GroupForm()
    
    context = {
        'recommended_groups': recommended_groups,
        'user_groups': user_groups,
        'form': form,
    }
    return render(request, 'core/groups.html', context)

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    is_member = request.user in group.members.all()
    posts = group.group_posts.all().order_by('-created_at')
    
    if not is_member and group.privacy == 'private':
        messages.warning(request, 'This is a private group. You need to be a member to view its content.')
        return redirect('groups')
    
    if request.method == 'POST':
        if 'join_group' in request.POST:
            group.members.add(request.user)
            return redirect('group_detail', group_id=group.id)
        if 'leave_group' in request.POST:
            group.members.remove(request.user)
            return redirect('groups')
        
        post_form = GroupPostForm(request.POST, request.FILES)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.group = group
            post.user = request.user
            post.save()
            return redirect('group_detail', group_id=group.id)
    else:
        post_form = GroupPostForm()
    
    context = {
        'group': group,
        'is_member': is_member,
        'posts': posts,
        'post_form': post_form,
    }
    return render(request, 'core/group_detail.html', context)

# ======================
# Group Chat Views
# ======================

@login_required
def group_chat(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if not group.members.filter(id=request.user.id).exists():
        messages.warning(request, "You need to be a member to access this group chat")
        return redirect('group_detail', group_id=group.id)
    
    messages = (GroupMessage.objects
                .filter(group=group)
                .select_related('sender')
                .order_by('-timestamp')[:50])
    
    members = (group.members
               .annotate(online=Count('last_seen', 
                      filter=Q(last_seen__gte=timezone.now()-timedelta(minutes=5))))
               .select_related('profile'))
    
    active_calls = (group.calls
                    .filter(ended_at__isnull=True)
                    .prefetch_related('participants'))
    
    # Mark notifications as read
    Notification.objects.filter(
        recipient=request.user,
        group=group,
        notification_type__in=['message', 'call'],
        is_read=False
    ).update(is_read=True)

    context = {
        'group': group,
        'messages': messages,
        'members': members,
        'active_calls': active_calls,
        'now': timezone.now(),
        'pusher_key': settings.PUSHER_APP_KEY if hasattr(settings, 'PUSHER_APP_KEY') else None,
    }
    return render(request, 'core/group_chat.html', context)

@require_POST
@login_required
def send_group_message(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if not group.members.filter(id=request.user.id).exists():
        return JsonResponse({'status': 'error', 'message': 'Not a member'}, status=403)
    
    try:
        data = json.loads(request.body)
        message_content = data.get('message', '').strip()
        
        if not message_content:
            return JsonResponse({'status': 'error', 'message': 'Message cannot be empty'}, status=400)
        
        message = GroupMessage.objects.create(
            group=group,
            sender=request.user,
            content=message_content
        )
        
        request.user.last_seen = timezone.now()
        request.user.save()
        
        response_data = {
            'status': 'success',
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'sender_avatar': request.build_absolute_uri(message.sender.profile_picture.url) if message.sender.profile_picture else '',
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'is_self': True,
            }
        }
        
        # If using Pusher or similar, trigger event here
        if hasattr(settings, 'PUSHER_APP_KEY'):
            try:
                import pusher
                pusher_client = pusher.Pusher(
                    app_id=settings.PUSHER_APP_ID,
                    key=settings.PUSHER_APP_KEY,
                    secret=settings.PUSHER_APP_SECRET,
                    cluster=settings.PUSHER_APP_CLUSTER,
                    ssl=True
                )
                pusher_client.trigger(
                    f'group-{group.id}',
                    'new-message',
                    response_data['message']
                )
            except Exception as e:
                logger.error(f"Error triggering Pusher event: {str(e)}")
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

@login_required
def get_group_messages(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if not group.members.filter(id=request.user.id).exists():
        return JsonResponse({'status': 'error', 'message': 'Not a member'}, status=403)
    
    last_message_id = request.GET.get('last_id', 0)
    
    try:
        last_message_id = int(last_message_id)
    except ValueError:
        last_message_id = 0
    
    messages = (GroupMessage.objects
                .filter(group=group, id__gt=last_message_id)
                .select_related('sender')
                .order_by('timestamp'))
    
    messages_data = []
    for message in messages:
        messages_data.append({
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'sender_avatar': request.build_absolute_uri(message.sender.profile_picture.url) if message.sender.profile_picture else '',
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'is_self': message.sender == request.user,
        })
    
    online_members = list(group.members.filter(
        last_seen__gte=timezone.now()-timedelta(minutes=5))
        .values('id', 'username', 'profile_picture'))
    
    return JsonResponse({
        'status': 'success',
        'messages': messages_data,
        'online_members': online_members,
    })

# ======================
# Group Call Views
# ======================

# @require_POST
# @login_required
# def start_group_call(request, group_id):
#     group = get_object_or_404(Group, id=group_id)
#     if not group.members.filter(id=request.user.id).exists():
#         return JsonResponse({'status': 'error', 'message': 'Not a member'}, status=403)
    
#     form = GroupCallForm(request.POST)
#     if not form.is_valid():
#         return JsonResponse({'status': 'error', 'message': 'Invalid call type'}, status=400)
    
#     call = form.save(commit=False)
#     call.group = group
#     call.creator = request.user
#     call.save()
#     call.participants.add(request.user)
    
#     if hasattr(settings, 'PUSHER_APP_KEY'):
#         try:
#             import pusher
#             pusher_client = pusher.Pusher(
#                 app_id=settings.PUSHER_APP_ID,
#                 key=settings.PUSHER_APP_KEY,
#                 secret=settings.PUSHER_APP_SECRET,
#                 cluster=settings.PUSHER_APP_CLUSTER,
#                 ssl=True
#             )
#             pusher_client.trigger(
#                 f'group-{group.id}',
#                 'call-started',
#                 {
#                     'call_id': call.id,
#                     'call_type': call.call_type,
#                     'creator': request.user.username,
#                     'start_time': call.started_at.strftime('%Y-%m-%d %H:%M:%S'),
#                 }
#             )
#         except Exception as e:
#             logger.error(f"Error triggering Pusher event: {str(e)}")
    
#     return JsonResponse({
#         'status': 'success',
#         'call_id': call.id,
#         'call_type': call.call_type,
#         'start_time': call.started_at.strftime('%Y-%m-%d %H:%M:%S'),
#     })

# @require_POST
# @login_required
# def end_group_call(request, call_id):
#     call = get_object_or_404(GroupCall, id=call_id)
#     if call.creator != request.user:
#         return JsonResponse({'status': 'error', 'message': 'Only call creator can end call'}, status=403)
    
#     call.ended_at = timezone.now()
#     call.save()
    
#     if hasattr(settings, 'PUSHER_APP_KEY'):
#         try:
#             import pusher
#             pusher_client = pusher.Pusher(
#                 app_id=settings.PUSHER_APP_ID,
#                 key=settings.PUSHER_APP_KEY,
#                 secret=settings.PUSHER_APP_SECRET,
#                 cluster=settings.PUSHER_APP_CLUSTER,
#                 ssl=True
#             )
#             pusher_client.trigger(
#                 f'group-{call.group.id}',
#                 'call-ended',
#                 {
#                     'call_id': call.id,
#                     'end_time': call.ended_at.strftime('%Y-%m-%d %H:%M:%S'),
#                 }
#             )
#         except Exception as e:
#             logger.error(f"Error triggering Pusher event: {str(e)}")
    
#     return JsonResponse({'status': 'success'})

# @login_required
# def join_group_call(request, call_id):
#     call = get_object_or_404(GroupCall, id=call_id)
#     if not call.group.members.filter(id=request.user.id).exists():
#         return JsonResponse({'status': 'error', 'message': 'Not a member'}, status=403)
    
#     call.participants.add(request.user)
    
#     participants = list(call.participants.values('id', 'username', 'profile_picture'))
    
#     if hasattr(settings, 'PUSHER_APP_KEY'):
#         try:
#             import pusher
#             pusher_client = pusher.Pusher(
#                 app_id=settings.PUSHER_APP_ID,
#                 key=settings.PUSHER_APP_KEY,
#                 secret=settings.PUSHER_APP_SECRET,
#                 cluster=settings.PUSHER_APP_CLUSTER,
#                 ssl=True
#             )
#             pusher_client.trigger(
#                 f'call-{call.id}',
#                 'participant-joined',
#                 {
#                     'user_id': request.user.id,
#                     'username': request.user.username,
#                     'participants': participants,
#                 }
#             )
#         except Exception as e:
#             logger.error(f"Error triggering Pusher event: {str(e)}")
    
#     return JsonResponse({
#         'status': 'success',
#         'participants': participants,
#     })

# @login_required
# def leave_group_call(request, call_id):
#     call = get_object_or_404(GroupCall, id=call_id)
#     if not call.participants.filter(id=request.user.id).exists():
#         return JsonResponse({'status': 'error', 'message': 'Not in call'}, status=400)
    
#     call.participants.remove(request.user)
    
#     participants = list(call.participants.values('id', 'username', 'profile_picture'))
    
#     if hasattr(settings, 'PUSHER_APP_KEY'):
#         try:
#             import pusher
#             pusher_client = pusher.Pusher(
#                 app_id=settings.PUSHER_APP_ID,
#                 key=settings.PUSHER_APP_KEY,
#                 secret=settings.PUSHER_APP_SECRET,
#                 cluster=settings.PUSHER_APP_CLUSTER,
#                 ssl=True
#             )
#             pusher_client.trigger(
#                 f'call-{call.id}',
#                 'participant-left',
#                 {
#                     'user_id': request.user.id,
#                     'username': request.user.username,
#                     'participants': participants,
#                 }
#             )
#         except Exception as e:
#             logger.error(f"Error triggering Pusher event: {str(e)}")
    
#     if call.participants.count() == 0:
#         call.ended_at = timezone.now()
#         call.save()
        
#         if hasattr(settings, 'PUSHER_APP_KEY'):
#             try:
#                 pusher_client.trigger(
#                     f'group-{call.group.id}',
#                     'call-ended',
#                     {
#                         'call_id': call.id,
#                         'end_time': call.ended_at.strftime('%Y-%m-%d %H:%M:%S'),
#                     }
#                 )
#             except Exception as e:
#                 logger.error(f"Error triggering Pusher event: {str(e)}")
    
#     return JsonResponse({
#         'status': 'success',
#         'participants': participants,
#     })

# @login_required
# def get_call_status(request, call_id):
    call = get_object_or_404(GroupCall, id=call_id)
    if not call.group.members.filter(id=request.user.id).exists():
        return JsonResponse({'status': 'error', 'message': 'Not a member'}, status=403)
    
    participants = list(call.participants.values('id', 'username', 'profile_picture'))
    
    return JsonResponse({
        'status': 'success',
        'call_id': call.id,
        'call_type': call.call_type,
        'creator_id': call.creator.id,
        'start_time': call.started_at.strftime('%Y-%m-%d %H:%M:%S'),
        'ended': call.ended_at is not None,
        'participants': participants,
    })

# ======================
# Utility Views
# ======================

@login_required
def update_user_presence(request):
    if request.user.is_authenticated:
        request.user.last_seen = timezone.now()
        request.user.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=401)

@login_required
def like_group_post(request, post_id):
    post = get_object_or_404(GroupPost, id=post_id)
    
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'count': post.likes.count()
    })

class EmailTestView(View):
    def get(self, request):
        try:
            send_mail(
                'Test Email Subject',
                'This is a test email body.',
                'from@example.com',
                ['to@example.com'],
                fail_silently=False,
            )
            return HttpResponse("Test email sent to console - check your server logs")
        except Exception as e:
            return HttpResponse(f"Email test failed: {str(e)}")
        
@login_required
def for_you(request):
    # Calculate the time 24 hours ago from now
    one_day_ago = timezone.now() - timedelta(days=1)
    
    # Get all posts from all users created in the last 24 hours
    posts = Post.objects.filter(
        created_at__gte=one_day_ago
    ).order_by('-created_at')
    
    context = {
        'posts': posts,
        'now': timezone.now(),
    }
    return render(request, 'core/for_you.html', context)


def group_delete(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        group.delete()
        return redirect('groups')  # Redirect to the groups page after deletion
    return render(request, 'core/group_confirm_delete.html', {'group': group})

def group_edit(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect('groups')  # Redirect to the groups page after saving
    else:
        form = GroupForm(instance=group)
    return render(request, 'core/group_edit.html', {'form': form, 'group': group})

def videocall(request):
    return render(request,'core/videocall.html', {'name': request.user.username })


from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def create_post(request):
    if request.method == 'POST':
        content = request.POST.get('content', '')
        image = request.FILES.get('image')
        video = request.FILES.get('video')

        post = Post.objects.create(user=request.user, content=content, image=image, video=video)
        return JsonResponse({'success': True, 'post': {
            'id': post.id,
            'content': post.content,
            'image': post.image.url if post.image else None,
            'video': post.video.url if post.video else None,
            'user': {
                'id': post.user.id,
                'username': post.user.username,
                'profile_picture': post.user.profile_picture.url,
            },
        }})
    return JsonResponse({'success': False, 'error': 'Invalid request'})