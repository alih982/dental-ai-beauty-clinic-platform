from django.urls import path
from django.views.generic import RedirectView
from config.dynamic_settings import settings

urlpatterns = [
    # Redirect all Django auth URLs to Next.js frontend - DYNAMIC URL
    path('login/', RedirectView.as_view(url=f"{settings.FRONTEND_URL}/login", permanent=False), name='login'),
    path('signup/', RedirectView.as_view(url=f"{settings.FRONTEND_URL}/signup", permanent=False), name='signUp'),
    path('logout/', RedirectView.as_view(url=settings.FRONTEND_URL, permanent=False), name='logout'),
]
