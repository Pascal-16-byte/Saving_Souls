from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    categories = models.ManyToManyField(Category, blank=True, related_name="users")

    def __str__(self):
        return self.user.username

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    categories = models.ManyToManyField(Category, blank=True, related_name='posts')
    sentiment = models.CharField(max_length=20, blank=True, null=True)
    distress_level = models.CharField(max_length=20, blank=True, null=True)

    @property
    def display_author(self):
        return "Anonymous" if self.anonymous else self.author.username

    def __str__(self):
        return f"{self.display_author()} - {self.content[:30]}"

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    anonymous = models.BooleanField(default=False)   # ✅ Make sure this exact line exists
    created_at = models.DateTimeField(auto_now_add=True)

    def display_author(self):
        return "Anonymous" if self.anonymous else self.author.username

    def __str__(self):
        return f"Comment by {self.display_author()} on {self.post.id}"
    
class Reaction(models.Model):
    REACTION_CHOICES = [
        ('heart', '❤️ Support'),
        ('hug', '🤗 Hug'),
        ('hands', '🙌 Appreciate'),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user', 'reaction_type')  # one reaction type per user per post

    def __str__(self):
        return f"{self.user.username} reacted {self.reaction_type} to Post {self.post.id}"

class Story(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Story"

class DistressAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    distress_level = models.CharField(max_length=20, blank=True, null=True)
    detected_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert from {self.user.username if self.user else 'Anonymous'} at {self.detected_at:%Y-%m-%d %H:%M}"
