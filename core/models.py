from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    categories = models.ManyToManyField(Category, blank=True, related_name="users")
    disclaimer_accepted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class Story(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    categories = models.ManyToManyField(Category, blank=True, related_name='stories')
    sentiment = models.CharField(max_length=20, blank=True, null=True)
    distress_level = models.CharField(max_length=20, blank=True, null=True)

    @property
    def display_author(self):
        return "Anonymous" if self.anonymous else self.author.username

    def __str__(self):
        return f"{self.display_author()} - {self.content[:30]}"

class Comment(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    anonymous = models.BooleanField(default=False)   # ✅ Make sure this exact line exists
    created_at = models.DateTimeField(auto_now_add=True)

    def display_author(self):
        return "Anonymous" if self.anonymous else self.author.username

    def __str__(self):
        return f"Comment by {self.display_author()} on {self.story.id}"
    
class Reaction(models.Model):
    REACTION_CHOICES = [
        ('heart', '❤️ Support'),
        ('hug', '🤗 Hug'),
        ('hands', '🙌 Appreciate'),
    ]

    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story', 'user', 'reaction_type')

    def __str__(self):
        return f"{self.user.username} reacted {self.reaction_type} to Story {self.story.id}"



class DistressAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    distress_level = models.CharField(max_length=20, blank=True, null=True)
    detected_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert from {self.user.username if self.user else 'Anonymous'} at {self.detected_at:%Y-%m-%d %H:%M}"

class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.name

class Journal(models.Model):
    MOOD_CHOICES = [
        ('neutral', 'Neutral'),
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('anxious', 'Anxious'),
        ('grateful', 'Grateful'),
        ('angry', 'Angry'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journals')
    title = models.CharField(max_length=150, blank=True, null=True)
    content = models.TextField(blank=True)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='journals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (self.title[:50] if self.title else f"Journal by {self.author.username} - {self.created_at.date()}")