from django.contrib import admin

from .models import CMSNavItem, CMSNavigation, CMSPage, CMSWidget, CMSWidgetPlacement


class CMSNavItemInline(admin.TabularInline):
    model = CMSNavItem
    extra = 1
    fields = ('title', 'parent', 'page', 'external_url', 'open_new_tab', 'sort_order', 'is_published')


@admin.register(CMSNavigation)
class CMSNavigationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_published', 'updated_at')
    list_filter = ('is_published',)
    search_fields = ('name', 'slug')
    inlines = [CMSNavItemInline]


class CMSWidgetPlacementInline(admin.TabularInline):
    model = CMSWidgetPlacement
    extra = 0
    fields = ('widget', 'slot', 'sort_order', 'is_published')


@admin.register(CMSPage)
class CMSPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'status', 'parent', 'navigation', 'nav_order', 'updated_at')
    list_filter = ('status', 'template', 'navigation')
    search_fields = ('title', 'slug', 'summary')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CMSWidgetPlacementInline]


@admin.register(CMSWidget)
class CMSWidgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_published', 'updated_at')
    list_filter = ('is_published',)
    search_fields = ('name', 'slug', 'title')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CMSWidgetPlacement)
class CMSWidgetPlacementAdmin(admin.ModelAdmin):
    list_display = ('widget', 'page', 'route_path', 'slot', 'sort_order', 'is_published')
    list_filter = ('slot', 'is_published')
    search_fields = ('widget__name', 'page__title', 'route_path')
