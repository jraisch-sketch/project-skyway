from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        PARENT = 'parent', 'Parent'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    grad_year = models.PositiveSmallIntegerField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    cycling_discipline = models.CharField(max_length=100, blank=True)
    email_verified = models.BooleanField(default=False)
    allowed_conferences = models.ManyToManyField(
        'schools.Conference',
        blank=True,
        related_name='conference_admin_users',
        help_text='Conferences this staff user can manage in Django Admin.',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self) -> str:
        return self.email


def default_access_code_expiry():
    return timezone.now() + timedelta(days=7)


class AccessCode(models.Model):
    code = models.CharField(max_length=64, unique=True)
    invitee_name = models.CharField(max_length=255, blank=True)
    invitee_email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(default=default_access_code_expiry)
    bound_device_id = models.CharField(max_length=128, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.code


class AccessCodeLog(models.Model):
    class Result(models.TextChoices):
        SUCCESS = 'success', 'Success'
        NOT_FOUND = 'not_found', 'Not found'
        INACTIVE = 'inactive', 'Inactive'
        EXPIRED = 'expired', 'Expired'
        DEVICE_MISMATCH = 'device_mismatch', 'Device mismatch'
        INVALID_INPUT = 'invalid_input', 'Invalid input'

    class Source(models.TextChoices):
        MANUAL = 'manual', 'Manual entry'
        COOKIE = 'cookie', 'Cookie check'

    access_code = models.ForeignKey(AccessCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    entered_code = models.CharField(max_length=64, blank=True)
    device_id = models.CharField(max_length=128, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=Source.choices)
    result = models.CharField(max_length=24, choices=Result.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.result} ({self.source})'
