from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FavoriteSchoolViewSet, SchoolViewSet, conferences_list, filter_options

router = DefaultRouter()
router.register(r'schools', SchoolViewSet, basename='school')
router.register(r'favorites', FavoriteSchoolViewSet, basename='favorite-school')

urlpatterns = [
    path('filters/', filter_options, name='filter-options'),
    path('conferences/', conferences_list, name='conference-list'),
    path('', include(router.urls)),
]
