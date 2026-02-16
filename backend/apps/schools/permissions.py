from rest_framework.permissions import BasePermission


class FavoritesPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'list' and request.query_params.get('public') == 'true':
            return True
        return bool(request.user and request.user.is_authenticated)
