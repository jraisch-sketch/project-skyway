from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AccessCodeCheckView,
    AccessCodeEnterView,
    ConfirmPasswordResetView,
    LoginView,
    MeView,
    RegisterView,
    RequestPasswordResetView,
    VerifyEmailView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', MeView.as_view(), name='me'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('password-reset/request/', RequestPasswordResetView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', ConfirmPasswordResetView.as_view(), name='password-reset-confirm'),
    path('access/check/', AccessCodeCheckView.as_view(), name='access-code-check'),
    path('access/enter/', AccessCodeEnterView.as_view(), name='access-code-enter'),
]
