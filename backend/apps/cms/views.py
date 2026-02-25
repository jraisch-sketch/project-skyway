from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import CMSNavigation, CMSPage, CMSWidgetPlacement, SiteConfiguration
from .serializers import (
    CMSNavigationSerializer,
    CMSPageSerializer,
    CMSWidgetPlacementSerializer,
    SiteConfigurationSerializer,
)


@api_view(['GET'])
def cms_page_detail(request, slug: str):
    page = (
        CMSPage.objects.select_related('navigation', 'parent')
        .filter(slug=slug, status=CMSPage.Status.PUBLISHED)
        .first()
    )
    if not page:
        return Response({'detail': 'Not found.'}, status=404)

    serializer = CMSPageSerializer(page)
    return Response(serializer.data)


@api_view(['GET'])
def cms_navigation_detail(request, slug: str):
    navigation = CMSNavigation.objects.filter(slug=slug, is_published=True).first()
    if not navigation:
        return Response({'detail': 'Not found.'}, status=404)

    serializer = CMSNavigationSerializer(navigation)
    return Response(serializer.data)


@api_view(['GET'])
def cms_widgets_for_route(request):
    route_path = (request.query_params.get('route_path') or '').strip()
    qs = CMSWidgetPlacement.objects.select_related('widget').filter(
        is_published=True,
        widget__is_published=True,
        page__isnull=True,
    )
    if route_path:
        qs = qs.filter(route_path=route_path)
    else:
        qs = qs.filter(route_path='')

    serializer = CMSWidgetPlacementSerializer(qs.order_by('slot', 'sort_order', 'id'), many=True)
    return Response(serializer.data)


@api_view(['GET'])
def cms_site_configuration(request):
    config = SiteConfiguration.load()
    serializer = SiteConfigurationSerializer(config)
    return Response(serializer.data)
