from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ('email', 'username', 'role', 'email_verified', 'is_staff', 'is_active')
    list_filter = ('role', 'email_verified', 'is_staff', 'is_active')
    ordering = ('email',)
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            'Student Profile',
            {'fields': ('role', 'grad_year', 'location', 'cycling_discipline', 'email_verified')},
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            'Student Profile',
            {'fields': ('email', 'role', 'grad_year', 'location', 'cycling_discipline', 'email_verified')},
        ),
    )
