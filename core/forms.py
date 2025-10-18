from django import forms
from .models import Post, Comment, Category, Profile, Story
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm, UserCreationForm

class SignUpForm(UserCreationForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="What are you going through?"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'categories']

    def save(self, commit=True):
        user = super().save(commit=commit)
        profile, created = Profile.objects.get_or_create(user=user)
        profile.categories.set(self.cleaned_data['categories'])
        if commit:
            profile.save()
        return user

class PostForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Share your story...'
        }),
        label='Story'
    )

    anonymous = forms.BooleanField(
        required=False,
        label='Post anonymously',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Post
        fields = ['content', 'anonymous', 'categories']


class CommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Write a supportive comment...'
        }),
        label='Comment'
    )

    anonymous = forms.BooleanField(
        required=False,
        label='Comment anonymously',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Comment
        fields = ['content', 'anonymous']

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class EditPasswordForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

from django import forms
from .models import Story, Category

class StoryForm(forms.ModelForm):
    anonymous = forms.BooleanField(
        required=False,
        label='Post Anonymously',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Story
        fields = ['content', 'category']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your story...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
