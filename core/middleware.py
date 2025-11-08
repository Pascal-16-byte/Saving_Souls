from django.shortcuts import redirect
from django.urls import reverse

class DisclaimerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            disclaimer_url = reverse('core:disclaimer')

            # Redirect if disclaimer not accepted (but allow access to disclaimer page)
            if profile and not profile.disclaimer_accepted and request.path != disclaimer_url:
                return redirect('core:disclaimer')

        return self.get_response(request)
