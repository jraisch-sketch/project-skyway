from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FavoriteSchoolViewSet, SchoolViewSet, filter_options

router = DefaultRouter()
router.register(r'schools', SchoolViewSet, basename='school')
router.register(r'favorites', FavoriteSchoolViewSet, basename='favorite-school')

urlpatterns = [
    path('filters/', filter_options, name='filter-options'),
    path('', include(router.urls)),
]
