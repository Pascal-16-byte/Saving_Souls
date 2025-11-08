from django.contrib import admin
from .models import Category, Profile, Story, Comment, Reaction, Journal, Tag
# Register your models here.

admin.site.register(Category)
admin.site.register(Profile)
admin.site.register(Story)
admin.site.register(Comment)
admin.site.register(Reaction)

@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'title', 'created_at', 'updated_at')
    list_filter = ('mood', 'created_at')
    search_fields = ('title', 'content', 'author__username')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
