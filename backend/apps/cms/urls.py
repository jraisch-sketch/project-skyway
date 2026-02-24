from django.urls import path

from .views import cms_navigation_detail, cms_page_detail, cms_widgets_for_route

urlpatterns = [
    path('pages/<slug:slug>/', cms_page_detail, name='cms-page-detail'),
    path('navigations/<slug:slug>/', cms_navigation_detail, name='cms-navigation-detail'),
    path('widgets/', cms_widgets_for_route, name='cms-widgets-route'),
]
