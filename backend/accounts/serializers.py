from django.contrib.auth.models import Group, Permission, User
from rest_framework import serializers

from accounts.permission_catalog import split_permission_code


class GroupSerializer(serializers.ModelSerializer):
    permission_codes = serializers.SerializerMethodField()
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        source="permissions",
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Group
        fields = ["id", "name", "permission_codes", "permission_ids"]

    def get_permission_codes(self, obj):
        return [
            f"{permission.content_type.app_label}.{permission.codename}"
            for permission in obj.permissions.select_related("content_type").all()
        ]

    def create(self, validated_data):
        permissions = validated_data.pop("permissions", [])
        group = Group.objects.create(**validated_data)
        group.permissions.set(permissions)
        return group

    def update(self, instance, validated_data):
        permissions = validated_data.pop("permissions", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if permissions is not None:
            instance.permissions.set(permissions)
        return instance


class PermissionOptionSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField()
    group = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)

    class Meta:
        model = Permission
        fields = ["id", "code", "label", "group"]

    def get_code(self, obj):
        return f"{obj.content_type.app_label}.{obj.codename}"


class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    group_ids = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), source="groups", many=True, write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    effective_permission_codes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_superuser",
            "groups",
            "group_ids",
            "password",
            "effective_permission_codes",
        ]
        read_only_fields = ["id", "is_superuser"]

    def get_effective_permission_codes(self, obj):
        if obj.is_superuser:
            return ["*"]
        permissions = Permission.objects.filter(group__user=obj).select_related("content_type").distinct()
        return sorted(f"{permission.content_type.app_label}.{permission.codename}" for permission in permissions)

    def create(self, validated_data):
        groups = validated_data.pop("groups", [])
        password = validated_data.pop("password", None) or "ChangeMe123!"
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        user.groups.set(groups)
        return user

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if request and request.user == instance and validated_data.get("is_active") is False:
            raise serializers.ValidationError("不能停用当前登录账号。")
        groups = validated_data.pop("groups", None)
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        if groups is not None:
            instance.groups.set(groups)
        return instance
