from rest_framework import serializers

from .models import CMSNavItem, CMSNavigation, CMSPage, CMSWidget, CMSWidgetPlacement


class CMSWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CMSWidget
        fields = ('id', 'name', 'slug', 'title', 'body')


class CMSWidgetPlacementSerializer(serializers.ModelSerializer):
    widget = CMSWidgetSerializer(read_only=True)

    class Meta:
        model = CMSWidgetPlacement
        fields = ('id', 'slot', 'sort_order', 'widget')


class CMSNavItemSerializer(serializers.ModelSerializer):
    page_slug = serializers.CharField(source='page.slug', read_only=True, default='')
    children = serializers.SerializerMethodField()

    class Meta:
        model = CMSNavItem
        fields = ('id', 'title', 'page_slug', 'external_url', 'open_new_tab', 'sort_order', 'children')

    def get_children(self, obj):
        serializer = CMSNavItemSerializer(
            obj.children.filter(is_published=True).order_by('sort_order', 'id'),
            many=True,
            context=self.context,
        )
        return serializer.data


class CMSNavigationSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = CMSNavigation
        fields = ('id', 'name', 'slug', 'description', 'items')

    def get_items(self, obj):
        roots = obj.items.filter(parent__isnull=True, is_published=True).order_by('sort_order', 'id')
        return CMSNavItemSerializer(roots, many=True, context=self.context).data


class CMSPageSerializer(serializers.ModelSerializer):
    parent_slug = serializers.CharField(source='parent.slug', read_only=True, default='')
    navigation = CMSNavigationSerializer(read_only=True)
    widgets = serializers.SerializerMethodField()

    class Meta:
        model = CMSPage
        fields = (
            'id',
            'title',
            'slug',
            'summary',
            'body',
            'template',
            'show_title',
            'show_sidebar_navigation',
            'parent_slug',
            'navigation',
            'widgets',
            'updated_at',
        )

    def get_widgets(self, obj):
        placements = (
            obj.widget_placements.select_related('widget')
            .filter(is_published=True, widget__is_published=True)
            .order_by('slot', 'sort_order', 'id')
        )
        return CMSWidgetPlacementSerializer(placements, many=True, context=self.context).data
