from datetime import timedelta

from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AccessCode, AccessCodeLog, User
from .serializers import (
    ConfirmPasswordResetSerializer,
    LoginSerializer,
    MeSerializer,
    RegisterSerializer,
    RequestPasswordResetSerializer,
)
from .utils import send_password_reset_email


def _client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _is_invitation_required():
    from apps.cms.models import SiteConfiguration

    return SiteConfiguration.load().invitation_code_required


def _create_access_log(
    *,
    request,
    source,
    result,
    access_code=None,
    entered_code='',
    device_id='',
):
    AccessCodeLog.objects.create(
        access_code=access_code,
        entered_code=entered_code,
        device_id=device_id,
        ip_address=_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        source=source,
        result=result,
    )


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Account created successfully. You can log in now.'}, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        if not uid or not token:
            return Response({'detail': 'uid and token are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Invalid verification link.'}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.email_verified = True
            user.save(update_fields=['email_verified'])
            return Response({'detail': 'Email verified successfully.'}, status=status.HTTP_200_OK)

        return Response({'detail': 'Verification token is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.get_full_name().strip() or user.username,
                    'account_type': user.role,
                    'grad_year': user.grad_year,
                },
            },
            status=status.HTTP_200_OK,
        )


class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if user:
            send_password_reset_email(user)
        return Response({'detail': 'If the account exists, a password reset email has been sent.'}, status=status.HTTP_200_OK)


class ConfirmPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ConfirmPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Reset token is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({'detail': 'Password reset successful.'}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AccessCodeEnterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not _is_invitation_required():
            return Response({'granted': True, 'invitation_code_required': False}, status=status.HTTP_200_OK)

        code = (request.data.get('code') or '').strip()
        device_id = (request.data.get('device_id') or '').strip()

        if not code or not device_id:
            _create_access_log(
                request=request,
                source=AccessCodeLog.Source.MANUAL,
                result=AccessCodeLog.Result.INVALID_INPUT,
                entered_code=code,
                device_id=device_id,
            )
            return Response({'detail': 'code and device_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        access_code = AccessCode.objects.filter(code=code).first()
        if not access_code:
            _create_access_log(
                request=request,
                source=AccessCodeLog.Source.MANUAL,
                result=AccessCodeLog.Result.NOT_FOUND,
                entered_code=code,
                device_id=device_id,
            )
            return Response({'detail': 'Invalid access code.'}, status=status.HTTP_403_FORBIDDEN)

        if not access_code.is_active:
            _create_access_log(
                request=request,
                source=AccessCodeLog.Source.MANUAL,
                result=AccessCodeLog.Result.INACTIVE,
                access_code=access_code,
                entered_code=code,
                device_id=device_id,
            )
            return Response({'detail': 'This access code is inactive.'}, status=status.HTTP_403_FORBIDDEN)

        if access_code.bound_device_id and access_code.bound_device_id != device_id:
            _create_access_log(
                request=request,
                source=AccessCodeLog.Source.MANUAL,
                result=AccessCodeLog.Result.DEVICE_MISMATCH,
                access_code=access_code,
                entered_code=code,
                device_id=device_id,
            )
            return Response({'detail': 'This code is already bound to another device.'}, status=status.HTTP_403_FORBIDDEN)

        now = timezone.now()
        access_code.bound_device_id = device_id
        if access_code.expires_at <= now:
            access_code.expires_at = now + timedelta(days=7)
        access_code.last_seen_at = now
        access_code.save(update_fields=['bound_device_id', 'expires_at', 'last_seen_at', 'updated_at'])

        _create_access_log(
            request=request,
            source=AccessCodeLog.Source.MANUAL,
            result=AccessCodeLog.Result.SUCCESS,
            access_code=access_code,
            entered_code=code,
            device_id=device_id,
        )
        return Response(
            {
                'granted': True,
                'expires_at': access_code.expires_at,
            },
            status=status.HTTP_200_OK,
        )


class AccessCodeCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not _is_invitation_required():
            return Response({'granted': True, 'invitation_code_required': False}, status=status.HTTP_200_OK)

        code = (request.data.get('code') or '').strip()
        device_id = (request.data.get('device_id') or '').strip()

        if not code or not device_id:
            _create_access_log(
                request=request,
                source=AccessCodeLog.Source.COOKIE,
                result=AccessCodeLog.Result.INVALID_INPUT,
                entered_code=code,
                device_id=device_id,
            )
            return Response({'detail': 'code and device_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        access_code = AccessCode.objects.filter(code=code).first()
        if not access_code:
            _create_access_log(
                request=request,
                source=AccessCodeLog.Source.COOKIE,
                result=AccessCodeLog.Result.NOT_FOUND,
                entered_code=code,
                device_id=device_id,
            )
            return Response({'detail': 'Invalid access code.'}, status=status.HTTP_403_FORBIDDEN)

        if not access_code.is_active:
            _create_access_log(
                request=request,
                source=AccessCodeLog.Source.COOKIE,
                result=AccessCodeLog.Result.INACTIVE,
                access_code=access_code,
                entered_code=code,
                device_id=device_id,
            )
            return Response({'detail': 'This access code is inactive.'}, status=status.HTTP_403_FORBIDDEN)

        if access_code.bound_device_id and access_code.bound_device_id != device_id:
            _create_access_log(
                request=request,
                source=AccessCodeLog.Source.COOKIE,
                result=AccessCodeLog.Result.DEVICE_MISMATCH,
                access_code=access_code,
                entered_code=code,
                device_id=device_id,
            )
            return Response({'detail': 'This code is already bound to another device.'}, status=status.HTTP_403_FORBIDDEN)

        if access_code.expires_at <= timezone.now():
            _create_access_log(
                request=request,
                source=AccessCodeLog.Source.COOKIE,
                result=AccessCodeLog.Result.EXPIRED,
                access_code=access_code,
                entered_code=code,
                device_id=device_id,
            )
            return Response({'detail': 'This code has expired. Re-enter to renew for one week.'}, status=status.HTTP_403_FORBIDDEN)

        if not access_code.bound_device_id:
            access_code.bound_device_id = device_id
        access_code.last_seen_at = timezone.now()
        access_code.save(update_fields=['bound_device_id', 'last_seen_at', 'updated_at'])

        _create_access_log(
            request=request,
            source=AccessCodeLog.Source.COOKIE,
            result=AccessCodeLog.Result.SUCCESS,
            access_code=access_code,
            entered_code=code,
            device_id=device_id,
        )
        return Response(
            {
                'granted': True,
                'expires_at': access_code.expires_at,
            },
            status=status.HTTP_200_OK,
        )
