from django.contrib import admin

from attachments.models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["file_name", "business_type", "business_id", "file_size", "uploader", "created_at"]
    list_filter = ["business_type"]
    search_fields = ["file_name", "business_id"]
