from rest_framework import serializers

from attachments.models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            "id",
            "file",
            "file_url",
            "file_name",
            "file_type",
            "file_size",
            "business_type",
            "business_id",
            "uploader",
            "created_at",
        ]
        read_only_fields = ["id", "file_url", "file_name", "file_type", "file_size", "uploader", "created_at"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url

    def create(self, validated_data):
        uploaded_file = validated_data["file"]
        validated_data["file_name"] = uploaded_file.name
        validated_data["file_type"] = getattr(uploaded_file, "content_type", "") or ""
        validated_data["file_size"] = uploaded_file.size
        validated_data["uploader"] = self.context["request"].user
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
