from rest_framework.permissions import BasePermission


def user_in_groups(user, names):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=names).exists()


class RolePermission(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        return user_in_groups(request.user, self.allowed_roles)


class IsAdminRole(RolePermission):
    allowed_roles = ("管理员",)


class IsSalesOrAdmin(RolePermission):
    allowed_roles = ("销售", "管理员")


class IsDesignerOrAdmin(RolePermission):
    allowed_roles = ("设计", "管理员")


class IsProductionOrAdmin(RolePermission):
    allowed_roles = ("生产", "管理员")


class IsFinanceOrAdmin(RolePermission):
    allowed_roles = ("财务", "管理员")
