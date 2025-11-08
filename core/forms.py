from django import forms
from .models import Comment, Category, Profile, Story, Journal, Tag
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

class StoryForm(forms.ModelForm):
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
        label='Share Anonymously',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Story
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

class JournalForm(forms.ModelForm):
    # allow a simple comma-separated tags input (optional)
    tags_input = forms.CharField(
        required=False,
        label="Tags (comma separated)",
        widget=forms.TextInput(attrs={"placeholder": "e.g. reflection, gratitude"})
    )

    class Meta:
        model = Journal
        fields = ['title', 'content', 'mood']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'style': 'color: white;', 'placeholder': 'Write as much or as little as you like...'}),
            'mood': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        # Accept an instance for edit-case to populate tags_input
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        if instance:
            tags_qs = instance.tags.all()
            if tags_qs.exists():
                self.fields['tags_input'].initial = ", ".join([t.name for t in tags_qs])

    def clean_tags_input(self):
        raw = self.cleaned_data.get('tags_input', '')
        # normalize: split, strip, unique
        tags = [t.strip() for t in raw.split(',') if t.strip()]
        return list(dict.fromkeys(tags))  # preserve order, unique

    def save(self, commit=True, author=None):
        journal = super().save(commit=False)
        if author and not journal.pk:
            journal.author = author
        if commit:
            journal.save()
            tags_list = self.cleaned_data.get('tags_input', [])
            # Set tags (create if necessary)
            journal.tags.clear()
            from .models import Tag
            for tname in tags_list:
                tag_obj, _ = Tag.objects.get_or_create(name=tname)
                journal.tags.add(tag_obj)
        return journal