from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=True, max_length=150)
    account_type = serializers.ChoiceField(
        write_only=True,
        choices=[User.Role.STUDENT, User.Role.PARENT],
        required=True,
    )
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    grad_year = serializers.IntegerField(required=True)

    class Meta:
        model = User
        fields = ('full_name', 'email', 'account_type', 'password', 'password_confirm', 'grad_year')

    def validate_full_name(self, value):
        value = value.strip()
        if len(value.split()) < 2:
            raise serializers.ValidationError('Enter your full name (first and last).')
        return value

    def validate_grad_year(self, value):
        current_year = timezone.now().year
        if value < current_year or value > current_year + 10:
            raise serializers.ValidationError(
                f'Graduation year must be between {current_year} and {current_year + 10}.'
            )
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def _unique_username_for_email(self, email: str) -> str:
        base = email.split('@')[0].strip().lower() or 'user'
        candidate = base
        suffix = 1
        while User.objects.filter(username=candidate).exists():
            suffix += 1
            candidate = f'{base}{suffix}'
        return candidate

    def create(self, validated_data):
        full_name = validated_data.pop('full_name').strip()
        account_type = validated_data.pop('account_type')
        password = validated_data.pop('password')
        validated_data.pop('password_confirm', None)
        first_name, _, last_name = full_name.partition(' ')
        user = User(**validated_data)
        user.first_name = first_name
        user.last_name = last_name.strip()
        user.username = self._unique_username_for_email(user.email)
        user.role = account_type
        user.email_verified = True
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        attrs['user'] = user
        return attrs


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ConfirmPasswordResetSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()

    def validate_new_password(self, value):
        validate_password(value)
        return value


class MeSerializer(serializers.ModelSerializer):
    account_type = serializers.CharField(source='role', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'account_type', 'grad_year', 'full_name')

    def get_full_name(self, obj):
        return obj.get_full_name().strip() or obj.username
