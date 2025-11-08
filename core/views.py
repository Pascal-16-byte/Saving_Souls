from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Comment, Reaction, Category, Story, DistressAlert, Journal, Tag
from .forms import  CommentForm, EditProfileForm, EditPasswordForm, SignUpForm, StoryForm, JournalForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q, F, Sum
from django.contrib.auth import update_session_auth_hash, login, get_user_model
from django.views.decorators.csrf import csrf_exempt
import json
# Import the analyze_sentiment function, generate_supportive_reply function
from .utils.ai_utils import analyze_sentiment, generate_supportive_reply
from django.core.mail import send_mail
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.timezone import now
from django.views.decorators.http import require_POST


def home(request):
    # Check if user has accepted the disclaimer
    if request.user.is_authenticated:
        profile = request.user.profile
        if not profile.disclaimer_accepted:
            return redirect('core:disclaimer')
    elif not request.session.get('disclaimer_accepted', False):
        return redirect('core:disclaimer')

    # Check if this is the user's first visit
    if not request.session.get('has_visited', False):
        request.session['has_visited'] = True
        show_welcome_modal = True
    else:
        show_welcome_modal = False

    # Check if we need to show the disclaimer
    show_disclaimer = request.session.pop('show_disclaimer', False)

    stories = Story.objects.all().order_by('-created_at')[:5]  # latest 5 stories

    for story in stories:
        # User's reactions
        if request.user.is_authenticated:
            story.user_reactions = story.reactions.filter(user=request.user).values_list('reaction_type', flat=True)
        else:
            story.user_reactions = []

        # Counts for all reactions
        story.reaction_counts = {
            'heart': story.reactions.filter(reaction_type='heart').count(),
            'hug': story.reactions.filter(reaction_type='hug').count(),
            'hands': story.reactions.filter(reaction_type='hands').count(),
        }

    return render(request, 'home.html', {
        'stories': stories,
        'show_welcome_modal': show_welcome_modal,
        'show_disclaimer': show_disclaimer
    })

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login the user
            return redirect('core:disclaimer')  # Redirect to disclaimer page
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

# def community(request):


def disclaimer(request):
    # Allow access to disclaimer page without login
    if request.user.is_authenticated:
        profile = request.user.profile
        if request.method == 'POST':
            profile.disclaimer_accepted = True
            profile.save()
            return redirect('core:home')
    else:
        # For non-authenticated users, use session to track acceptance
        if request.method == 'POST':
            request.session['disclaimer_accepted'] = True
            return redirect('core:home')
    
    return render(request, 'disclaimer.html')

User = get_user_model()

@login_required
def create_story(request):
    categories_qs = Category.objects.all()
    selected_categories = []

    if request.method == 'POST':
        # capture selected category ids (strings) so template can render checked state
        selected_categories = request.POST.getlist('categories')

        form = StoryForm(request.POST)
        if form.is_valid():
            # save story instance (commit=False so we can set author)
            story = form.save(commit=False)
            story.author = request.user
            story.save()

            # If the form contains M2M fields (like form.categories) use save_m2m()
            try:
                form.save_m2m()
            except Exception:
                # If categories were submitted as raw inputs (name="categories"), attach them manually
                if selected_categories:
                    try:
                        # convert to ints and fetch category objects
                        cat_ids = [int(cid) for cid in selected_categories if cid]
                        cats = Category.objects.filter(id__in=cat_ids)
                        # assumes Story model has a ManyToManyField called categories
                        story.categories.set(cats)
                    except Exception as e:
                        # non-fatal, log and continue
                        print(f"⚠ Could not attach categories: {e}")

            # 🧠 AI Sentiment Analysis (same as your original logic)
            try:
                analysis = analyze_sentiment(story.content)
                sentiment = analysis.get("sentiment")
                distress_level = analysis.get("distress_level")
                print(f"Story analysis - Sentiment: {sentiment}, Distress Level: {distress_level}")
            except Exception as e:
                print(f"⚠ AI analysis error: {e}")
                sentiment = None
                distress_level = None

            # 💬 Auto-support message for distress
            if distress_level == "high":
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
                    send_mail(subject, message, "Saving_Souls <noreply@savingsouls.com>", list(admins))
                    print("📧 Email alert sent to admins!")
                except Exception as e:
                    print(f"⚠ AI Support or email error: {e}")

            messages.success(request, "Your story has been posted successfully!")
            return redirect('core:my_stories')

        else:
            # If form invalid, fall through to re-render template with the form (errors will show)
            print("Form invalid:", form.errors)

    else:
        form = StoryForm()

    # Provide categories and selected_categories for template rendering
    context = {
        'form': form,
        'categories': categories_qs,
        'selected_categories': selected_categories,
    }
    return render(request, 'create_story.html', context)
    
def story_detail(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    comments = story.comments.all().order_by('-created_at')

    # Determine which reactions the current user has already made
    user_reactions = []
    if request.user.is_authenticated:
        user_reactions = story.reactions.filter(user=request.user).values_list('reaction_type', flat=True)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.story = story
            comment.author = request.user
            comment.save()
            return redirect('core:story_detail', story_id=story.id)
    else:
        form = CommentForm()

    return render(request, 'story_detail.html', {
        'story': story,
        'comments': comments,
        'form': form,
        'user_reactions': user_reactions
    })

def stories(request):
    search_query = request.GET.get("q", "")
    category_id = request.GET.get("category", "")

    # ✅ Use Story model instead of Post
    stories_list = Story.objects.all().order_by("-created_at")

    if search_query:
        stories_list = stories_list.filter(content__icontains=search_query)

    if category_id:
        stories_list = stories_list.filter(category_id=category_id)

    # 🧠 Add reaction counts and user reactions
    for story in stories_list:
        story.reaction_counts = {
            "heart": story.reactions.filter(reaction_type="heart").count(),
            "hug": story.reactions.filter(reaction_type="hug").count(),
            "hands": story.reactions.filter(reaction_type="hands").count(),
        }
        story.user_reactions = []
        if request.user.is_authenticated:
            story.user_reactions = story.reactions.filter(user=request.user).values_list(
                "reaction_type", flat=True
            )
        story.total_reactions = sum(story.reaction_counts.values())

    # 🔥 Top reacted stories
    top_stories = sorted(stories_list, key=lambda x: x.total_reactions, reverse=True)[:3]

    # 📄 Pagination
    paginator = Paginator(stories_list, 5)
    page_number = request.GET.get("page")
    stories = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(
        request,
        "stories.html",
        {
            "stories": stories,
            "top_stories": top_stories,
            "search_query": search_query,
            "categories": categories,
            "selected_category": category_id,
        },
    )


@login_required
def react_to_story(request, story_id, reaction_type):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=403)

    story = get_object_or_404(Story, id=story_id)
    reaction, created = Reaction.objects.get_or_create(user=request.user, story=story)

    # Toggle reaction
    if not created and reaction.reaction_type == reaction_type:
        reaction.delete()
        reacted = None
    else:
        reaction.reaction_type = reaction_type
        reaction.save()
        reacted = reaction_type

    # Return updated counts
    counts = {
        "heart": story.reactions.filter(reaction_type="heart").count(),
        "hug": story.reactions.filter(reaction_type="hug").count(),
        "hands": story.reactions.filter(reaction_type="hands").count(),
    }

    return JsonResponse({"reactions_count": counts, "reacted": reacted})


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
    stories = Story.objects.filter(author=request.user)
    return render(request, "my_stories.html", {"stories": stories})

@login_required
def edit_story(request, pk):
    """
    Edit an existing story. Only the author or a superuser may edit.
    Preserves category chip selections via selected_categories.
    Re-runs sentiment analysis on save and triggers the same 'high distress'
    flow as create_story (AI reply + admin email).
    """
    story = get_object_or_404(Story, pk=pk)

    # Permission: allow only author or superusers
    if request.user != story.author and not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to edit this story.")

    categories_qs = Category.objects.all()
    selected_categories = []

    if request.method == 'POST':
        # capture category selections (strings)
        selected_categories = request.POST.getlist('categories')
        form = StoryForm(request.POST, instance=story)

        if form.is_valid():
            story = form.save(commit=False)
            # keep the original author
            story.author = story.author
            story.save()

            # try to save M2M fields from form; fallback to manual attach
            try:
                form.save_m2m()
            except Exception:
                if selected_categories:
                    try:
                        cat_ids = [int(cid) for cid in selected_categories if cid]
                        cats = Category.objects.filter(id__in=cat_ids)
                        story.categories.set(cats)
                    except Exception as e:
                        print(f"⚠ Could not attach categories on edit: {e}")

            # Re-run AI sentiment analysis (optional but consistent with create)
            try:
                analysis = analyze_sentiment(story.content)
                sentiment = analysis.get("sentiment")
                distress_level = analysis.get("distress_level")
                print(f"[edit] Story analysis - Sentiment: {sentiment}, Distress Level: {distress_level}")
            except Exception as e:
                print(f"⚠ AI analysis error on edit: {e}")
                sentiment = None
                distress_level = None

            # If distress high, create supportive reply and notify admins
            if distress_level == "high":
                try:
                    supportive_text = generate_supportive_reply(story.content)
                    ai_user, _ = User.objects.get_or_create(
                        username="AI_Support",
                        defaults={"is_active": False}
                    )
                    Comment.objects.create(story=story, author=ai_user, content=supportive_text)

                    admins = User.objects.filter(is_superuser=True).values_list("email", flat=True)
                    subject = f"🚨 Distress Alert (edited): {story.author.username} may need help"
                    message = (
                        f"A story edited by {story.author.username} shows signs of high distress.\n\n"
                        f"Story content:\n\"{story.content}\"\n\n"
                        f"Auto Supportive Reply:\n\"{supportive_text}\"\n\n"
                        "Please review it in the admin panel or reach out if needed."
                    )
                    send_mail(subject, message, "Saving_Souls <noreply@savingsouls.com>", list(admins))
                    print("📧 Email alert sent to admins (edit)!")
                except Exception as e:
                    print(f"⚠ AI Support or email error on edit: {e}")

            messages.success(request, "Your story has been updated.")
            return redirect('core:my_stories')
        else:
            print("Form invalid on edit:", form.errors)

    else:
        # Prefill the form with instance data
        form = StoryForm(instance=story)
        # For initial checked chips, use story.categories if present
        try:
            selected_categories = [str(c.id) for c in story.categories.all()]
        except Exception:
            selected_categories = []

    context = {
        'form': form,
        'categories': categories_qs,
        'selected_categories': selected_categories,
        'story': story,
    }
    return render(request, 'create_story.html', context)  # reuse create template or use edit template

@login_required
def delete_story(request, story_id):
    story = get_object_or_404(Story, id=story_id, author=request.user)
    if request.method == 'POST':
        story.delete()
        messages.success(request, 'Your story has been deleted.')
        return redirect('core:my_stories')
    return render(request, 'delete_story.html', {'story': story})

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
#         except Exception as e:
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
@login_required
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

@login_required
def journals(request):
    qs = Journal.objects.filter(author=request.user).order_by('-created_at')
    paginator = Paginator(qs, 8)
    page = request.GET.get('page')
    journals_page = paginator.get_page(page)
    return render(request, 'journals.html', {'journals': journals_page})

@login_required
def create_journal(request):
    if request.method == 'POST':
        form = JournalForm(request.POST)
        if form.is_valid():
            form.save(commit=True, author=request.user)
            messages.success(request, 'Journal entry saved.')
            return redirect('core:journals')
    else:
        form = JournalForm()
    return render(request, 'create_journal.html', {'form': form})

@login_required
def journal_detail(request, journal_id):
    journal = get_object_or_404(Journal, id=journal_id, author=request.user)
    return render(request, 'journal_detail.html', {'journal': journal})

@login_required
def edit_journal(request, journal_id):
    journal = get_object_or_404(Journal, id=journal_id, author=request.user)
    if request.method == 'POST':
        form = JournalForm(request.POST, instance=journal)
        if form.is_valid():
            form.save(commit=True, author=request.user)
            messages.success(request, 'Journal entry updated.')
            return redirect('core:journal_detail', journal_id=journal.id)
    else:
        form = JournalForm(instance=journal)
    return render(request, 'create_journal.html', {'form': form, 'is_edit': True})

@login_required
def delete_journal(request, journal_id):
    journal = get_object_or_404(Journal, id=journal_id, author=request.user)
    if request.method == 'POST':
        journal.delete()
        messages.success(request, 'Journal entry deleted.')
        return redirect('core:journals')
    # optional: confirm page or just redirect back
    return redirect('core:journal_detail', journal_id=journal.id)