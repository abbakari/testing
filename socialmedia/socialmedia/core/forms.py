from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from .models import User, Post, Comment, Group, GroupPost, GroupMessage
from django.contrib.auth.models import Group as AuthGroup
from django.utils import timezone
from .models import GroupCall


# User Forms
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'profile_picture', 'bio')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'profile_picture', 'bio', 'location', 'birth_date')


# Post and Comment Forms
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'media_file']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': "What's on your mind?"}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write a comment...'}),
        }


# Password Forms
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'class': 'form-control',
            'placeholder': 'Enter your email',
        }),
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
        }),
    )
    new_password2 = forms.CharField(
        label="New password confirmation",
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
        }),
    )


# Group Forms
class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'banner', 'avatar', 'category', 'privacy']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'creator' in self.fields:  # Ensure 'creator' exists before disabling
            self.fields['creator'].disabled = True


class GroupPostForm(forms.ModelForm):
    class Meta:
        model = GroupPost
        fields = ['content', 'media_file']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': "Share something with the group..."}),
        }


class GroupMessageForm(forms.ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'placeholder': 'Type a message...'}),
        }
        
        
class GroupCallForm(forms.ModelForm):
    call_type = forms.ChoiceField(
        choices=GroupCall.CALL_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='video'
    )
    
    class Meta:
        model = GroupCall
        fields = ['call_type']
        widgets = {
            'call_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }
        
        

