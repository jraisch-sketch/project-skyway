from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone
from datetime import timedelta
from hijack.contrib.admin import HijackUserAdminMixin

from .models import AccessCode, AccessCodeLog, User


def is_conference_admin_user(user):
    return bool(user.is_active and user.is_staff and not user.is_superuser)


@admin.register(User)
class UserAdmin(HijackUserAdminMixin, DjangoUserAdmin):
    model = User
    list_display = ('email', 'username', 'role', 'email_verified', 'is_staff', 'is_active')
    list_filter = ('role', 'email_verified', 'is_staff', 'is_active')
    ordering = ('email',)
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            'Student Profile',
            {'fields': ('role', 'grad_year', 'location', 'cycling_discipline', 'email_verified')},
        ),
        (
            'Conference Administrator',
            {'fields': ('allowed_conferences',)},
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            'Student Profile',
            {'fields': ('email', 'role', 'grad_year', 'location', 'cycling_discipline', 'email_verified')},
        ),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        if not request.user.is_superuser:
            fieldsets = [fs for fs in fieldsets if fs[0] != 'Conference Administrator']
        return fieldsets

    def has_module_permission(self, request):
        if is_conference_admin_user(request.user):
            return False
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if is_conference_admin_user(request.user):
            return False
        return super().has_view_permission(request, obj=obj)


@admin.register(AccessCode)
class AccessCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'invitee_name',
        'invitee_email',
        'is_active',
        'expires_at',
        'bound_device_id',
        'last_seen_at',
        'created_at',
    )
    list_filter = ('is_active',)
    search_fields = ('code', 'invitee_name', 'invitee_email', 'bound_device_id')
    readonly_fields = ('created_at', 'updated_at', 'last_seen_at')
    actions = ('extend_one_week', 'disable_codes', 'enable_codes', 'clear_device_binding')

    def has_module_permission(self, request):
        if is_conference_admin_user(request.user):
            return False
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if is_conference_admin_user(request.user):
            return False
        return super().has_view_permission(request, obj=obj)

    def extend_one_week(self, request, queryset):
        queryset.update(expires_at=timezone.now() + timedelta(days=7))
    extend_one_week.short_description = 'Extend selected codes by 1 week from now'

    def disable_codes(self, request, queryset):
        queryset.update(is_active=False)
    disable_codes.short_description = 'Disable selected codes'

    def enable_codes(self, request, queryset):
        queryset.update(is_active=True)
    enable_codes.short_description = 'Enable selected codes'

    def clear_device_binding(self, request, queryset):
        queryset.update(bound_device_id='')
    clear_device_binding.short_description = 'Clear device lock for selected codes'


@admin.register(AccessCodeLog)
class AccessCodeLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'source', 'result', 'access_code', 'entered_code', 'ip_address', 'device_id')
    list_filter = ('source', 'result', 'created_at')
    search_fields = ('entered_code', 'ip_address', 'device_id', 'access_code__code')
    readonly_fields = (
        'access_code',
        'entered_code',
        'device_id',
        'ip_address',
        'user_agent',
        'source',
        'result',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_module_permission(self, request):
        if is_conference_admin_user(request.user):
            return False
        return super().has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        if is_conference_admin_user(request.user):
            return False
        return super().has_view_permission(request, obj=obj)
