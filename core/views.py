from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Post, Comment, Reaction, Category, Profile, Story, DistressAlert
from .forms import PostForm, CommentForm, EditProfileForm, EditPasswordForm, SignUpForm, StoryForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q, F, Sum
from django.contrib.auth import update_session_auth_hash, login
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI,OpenAIError
import json
import os, random
# Import the analyze_sentiment function, generate_supportive_reply function
from .utils.ai_utils import analyze_sentiment, generate_supportive_reply
from django.core.mail import send_mail
from django.contrib.admin.views.decorators import staff_member_required
from .utils.emotion_utils import detect_emotion
from django.utils.timezone import now
from django.views.decorators.http import require_POST

def home(request):
    posts = Post.objects.all().order_by('-created_at')[:5]  # latest 5 posts

    for post in posts:
        # User's reactions
        post.user_reactions = []
        if request.user.is_authenticated:
            post.user_reactions = post.reactions.filter(user=request.user).values_list('reaction_type', flat=True)

        # Counts for all reactions
        post.reaction_counts = {
            'heart': post.reactions.filter(reaction_type='heart').count(),
            'hug': post.reactions.filter(reaction_type='hug').count(),
            'hands': post.reactions.filter(reaction_type='hands').count(),
        }

    return render(request, 'home.html', {'posts': posts})

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

# def community(request):
#     posts = Post.objects.all().order_by('-created_at')
#     return render(request, 'community.html', {'posts': posts})

@login_required
def all_stories(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect('core:stories')

    stories = Story.objects.select_related('user', 'category').order_by('-created_at')
    return render(request, 'admin_view.html', {'stories': stories})


@login_required
def create_post(request):
    if request.method == 'POST':
        content = request.POST.get("content")
        category_id = request.POST.get("category")
        author=request.user if not is_anonymous else None,
        is_anonymous=is_anonymous,

        # 🧩 Handle missing content
        if not content:
            messages.error(request, "Story content cannot be empty.")
            return redirect("core:create_post")

        # ✅ Fetch category safely
        category = None
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                category = None

        # ✅ Create Story instance
        story = Story.objects.create(
            user=request.user,
            category=category,
            content=content,
            author=request.user if not is_anonymous else None,
            is_anonymous=is_anonymous,
        )

        # 🧠 AI Sentiment Analysis
        try:
            analysis = analyze_sentiment(story.content)
            story.sentiment = analysis.get("sentiment")
            story.distress_level = analysis.get("distress_level")
            story.save()
        except Exception as e:
            print(f"⚠️ AI analysis error: {e}")

        # 💬 Auto-support message for distress
        if getattr(story, "distress_level", None) == "high":
            try:
                supportive_text = generate_supportive_reply(story.content)
                ai_user, _ = User.objects.get_or_create(username="AI_Support", defaults={"is_active": False})
                Comment.objects.create(story=story, author=ai_user, content=supportive_text)

                # 📧 Notify admins
                admins = User.objects.filter(is_superuser=True).values_list("email", flat=True)
                subject = f"🚨 Distress Alert: {request.user.username} may need help"
                message = (
                    f"A new story by {request.user.username} shows signs of high distress.\n\n"
                    f"Story content:\n\"{story.content}\"\n\n"
                    f"Auto Supportive Reply:\n\"{supportive_text}\"\n\n"
                    "Please review it in the admin panel or reach out if needed."
                )
                send_mail(subject, message, "Saving_Souls <noreply@savingsouls.com>", admins)
                print("📧 Email alert sent to admins!")

            except Exception as e:
                print(f"⚠️ AI Support or email error: {e}")

        messages.success(request, "Your story has been posted successfully!")
        return redirect('core:my_stories')

    # GET request → render form
    categories = Category.objects.all()
    return render(request, 'create_post.html', {'categories': categories})

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all().order_by('-created_at')

    # Determine which reactions the current user has already made
    user_reactions = []
    if request.user.is_authenticated:
        user_reactions = post.reactions.filter(user=request.user).values_list('reaction_type', flat=True)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('core:post_detail', post_id=post.id)
    else:
        form = CommentForm()

    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'user_reactions': user_reactions
    })

def stories(request):
    search_query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    posts_list = Post.objects.all().order_by('-created_at')

    if search_query:
        posts_list = posts_list.filter(content__icontains=search_query)

    if category_id:
        posts_list = posts_list.filter(categories__id=category_id)

    # Add reaction counts and user reactions
    for post in posts_list:
        post.reaction_counts = {
            'heart': post.reactions.filter(reaction_type='heart').count(),
            'hug': post.reactions.filter(reaction_type='hug').count(),
            'hands': post.reactions.filter(reaction_type='hands').count(),
        }
        post.user_reactions = []
        if request.user.is_authenticated:
            post.user_reactions = post.reactions.filter(user=request.user).values_list('reaction_type', flat=True)
        post.total_reactions = sum(post.reaction_counts.values())

    # Top reacted posts
    top_posts = sorted(posts_list, key=lambda x: x.total_reactions, reverse=True)[:3]

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(posts_list, 5)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(request, 'stories.html', {
        'posts': posts,
        'top_posts': top_posts,
        'search_query': search_query,
        'categories': categories,
        'selected_category': category_id
    })

@login_required
def react_to_post(request, post_id, reaction_type):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=403)

    post = get_object_or_404(Post, id=post_id)
    reaction, created = Reaction.objects.get_or_create(user=request.user, post=post)

    # Toggle reaction
    if reaction.reaction_type == reaction_type:
        reaction.delete()
        reacted = None
    else:
        reaction.reaction_type = reaction_type
        reaction.save()
        reacted = reaction_type

    # Return updated counts
    counts = {
        'heart': post.reactions.filter(reaction_type='heart').count(),
        'hug': post.reactions.filter(reaction_type='hug').count(),
        'hands': post.reactions.filter(reaction_type='hands').count(),
    }

    return JsonResponse({'reactions_count': counts, 'reacted': reacted})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        profile_form = EditProfileForm(request.POST, instance=request.user)
        password_form = EditPasswordForm(user=request.user, data=request.POST)
        
        if 'update_profile' in request.POST and profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('core:edit_profile')
        
        if 'update_password' in request.POST and password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Password updated successfully.')
            return redirect('core:edit_profile')
    else:
        profile_form = EditProfileForm(instance=request.user)
        password_form = EditPasswordForm(user=request.user)

    return render(request, 'edit_profile.html', {
        'profile_form': profile_form,
        'password_form': password_form
    })

@login_required
def my_stories(request):
    stories = Story.objects.filter(user=request.user)
    return render(request, "my_stories.html", {"stories": stories})

@login_required
def edit_post(request, post_id):
    story = get_object_or_404(Story, id=post_id, user=request.user)  # remove user filter for now

    if request.method == 'POST':
        form = StoryForm(request.POST, instance=story)
        if form.is_valid():
            story = form.save(commit=False)
            if story.user is None:  # auto-fix missing user
                story.user = request.user
            story.save()
            return redirect('core:my_stories')
    else:
        form = StoryForm(instance=story)

    return render(request, 'edit_post.html', {'form': form})

@login_required
def delete_post(request, story_id):
    story = get_object_or_404(Story, id=story_id)

    # ✅ Allow deletion only if the user is the owner or an admin
    if request.user == story.user or request.user.is_staff or request.user.is_superuser:
        if request.method == 'POST':
            story.delete()
            messages.success(request, "Story deleted successfully.")
            # Redirect appropriately based on user type
            if request.user.is_staff or request.user.is_superuser:
                return redirect('core:stories')  # Admins see all stories
            else:
                return redirect('core:my_stories')
    else:
        messages.error(request, "You do not have permission to delete this story.")
        return redirect('core:stories')

    return redirect('core:stories')

# 🩵 Mock fallback responses
MOCK_RESPONSES = [
    "I'm really sorry you're feeling this way. You're not alone — I'm here to listen. 💬",
    "That sounds difficult. Have you had a chance to talk to someone you trust about this?",
    "It's okay to feel stressed sometimes. Remember to take a deep breath. 🌿",
    "You're doing your best, and that’s enough for now. ❤️",
    "I'm proud of you for sharing how you feel. That takes courage. 🌟"
]

def chat_page(request):
    return render(request, 'chatbot.html')

# @csrf_exempt
# @login_required
# def ai_chat(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body.decode("utf-8"))
#             user_message = data.get("message", "").strip()
#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON data"}, status=400)

#         if not user_message:
#             return JsonResponse({"reply": "Please share how you’re feeling 💬"})

#         # 🧠 Step 1: Emotion detection
#         emotion, confidence, all_emotions = detect_emotion(user_message)
#         print(f"🎭 Detected Emotion: {emotion} ({confidence:.2f})")

#         # 🧩 Step 2: Distress detection
#         distress_flag, distress_level = analyze_sentiment(user_message)

#         # 💬 Step 3: Generate supportive reply
#         try:
#             base_reply = generate_supportive_reply(user_message)
#         except OpenAIError as e:
#             print(f"❌ AI Supportive Reply Error: {e}")
#             base_reply = None

#         # 🩹 Fallback message
#         if not base_reply:
#             base_reply = random.choice(MOCK_RESPONSES)

#         # 💡 Emotion-personalized AI response
#         emotion_based_prefix = {
#             "sadness": "I sense some sadness in your words. 💙",
#             "anger": "It seems like you're upset — that’s completely okay. 💢",
#             "fear": "That sounds scary or worrying. You’re not alone. 🌧️",
#             "joy": "That’s wonderful to hear! 😊",
#             "disgust": "That must have been unpleasant. I'm here to listen. 💬",
#             "surprise": "That sounds unexpected! Tell me more. 🤔"
#         }.get(emotion, "Thank you for sharing how you feel.")

#         final_reply = f"{emotion_based_prefix} {base_reply}"

#         # 🚨 Step 4: Log distress if detected
#         if distress_flag:
#             DistressAlert.objects.create(
#                 user=request.user,
#                 message=user_message,
#                 distress_level=distress_level,
#             )
#             print(f"🚨 Distress alert: {request.user.username} — {user_message}")

#         # 🧾 Step 5: Send back emotion + AI response
#         return JsonResponse({
#             "reply": final_reply,
#             "emotion": emotion,
#             "emotion_confidence": round(confidence, 2),
#             "distress_detected": distress_flag,
#             "distress_level": distress_level,
#         })

#     return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
@require_POST
def ask_ai(request):
    """
    Handles user messages from the chatbot.
    Returns a JSON response with the AI-generated reply.
    """
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()

        if not user_message:
            return JsonResponse({"reply": "Please enter a message."}, status=400)

        # 1️⃣ Analyze emotional tone or distress level
        sentiment_data = analyze_sentiment(user_message)
        distress_flag = sentiment_data.get("distress_flag", "false")
        distress_level = sentiment_data.get("distress_level", "unknown")

        # 2️⃣ Generate empathetic AI reply
        ai_reply = generate_supportive_reply(user_message)

        # 3️⃣ Save distress alerts if distress_flag is true
        if distress_flag == "true":
            DistressAlert.objects.create(
                message=user_message,
                distress_level=distress_level,
                detected_at=now()
            )
            print(f"🚨 Distress Alert Logged: {distress_level.upper()} - {user_message}")

        # 4️⃣ Return AI reply to frontend
        return JsonResponse({
            "reply": ai_reply,
            "distress_flag": distress_flag,
            "distress_level": distress_level,
        })

    except json.JSONDecodeError:
        return JsonResponse({"reply": "Invalid JSON format."}, status=400)
    except Exception as e:
        print(f"❌ Error in ask_ai: {e}")
        return JsonResponse({"reply": "Sorry, something went wrong on the server."}, status=500)

@staff_member_required
def distress_alerts(request):
    alerts = DistressAlert.objects.order_by('-detected_at')
    return render(request, 'distress_alert.html', {'alerts': alerts})

def delete_alert(request, alert_id):
    alert = get_object_or_404(DistressAlert, id=alert_id)
    if request.method == "POST":
        alert.delete()
    return redirect("core:distress_alerts")