from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, Permission, User
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.permission_catalog import PERMISSION_CATALOG, split_permission_code
from accounts.serializers import GroupSerializer, UserSerializer
from common.permissions import IsAdminRole


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"code": "INVALID_CREDENTIALS", "message": "用户名或密码错误"}, status=status.HTTP_400_BAD_REQUEST)
    login(request, user)
    return Response(UserSerializer(user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"message": "已退出"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related("groups").order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]

    @action(detail=False, methods=["get"])
    def roles(self, request):
        return Response(GroupSerializer(Group.objects.order_by("name"), many=True).data)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.prefetch_related("permissions__content_type").order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [IsAdminRole]

    @action(detail=False, methods=["get"])
    def permissions(self, request):
        permissions = []
        for item in PERMISSION_CATALOG:
            app_label, codename = split_permission_code(item["code"])
            try:
                permission = Permission.objects.select_related("content_type").get(
                    content_type__app_label=app_label,
                    codename=codename,
                )
            except Permission.DoesNotExist:
                continue
            permissions.append(
                {
                    "id": permission.id,
                    "code": item["code"],
                    "label": item["label"],
                    "group": item["group"],
                }
            )
        return Response(permissions)
