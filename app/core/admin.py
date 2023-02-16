"""
Django admin Customization
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core import models
from django.utils.translation import gettext_lazy as _


class UserAdmin(BaseUserAdmin):
    """Define admin pages for users"""
    ordering = ["id"]
    list_display = ["email", "name"]
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            _('permisssions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            }
        ),
        (_('Important dates'), {'fields': ('last_login',)})

    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide', ),
            'fields': (
                'email',
                'is_active',
                'is_staff',
                'is_superuser',
                'name',
                'password1',
                'password2',
            )
        }),
    )


admin.site.register(models.User, UserAdmin)
