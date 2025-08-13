from rest_framework.permissions import BasePermission
from mongo_models import MongoUser

class IsAdmin(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        user = MongoUser.get_by_email(request.user.email)
        return user and user.role == 'admin'
