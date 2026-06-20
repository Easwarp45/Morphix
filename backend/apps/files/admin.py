from django.contrib import admin

from .models import File


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "user", "file_extension", "file_size", "status", "created_at")
    list_filter = ("status", "file_extension", "created_at")
    search_fields = ("original_name", "user__email")
    readonly_fields = ("id", "s3_key", "stored_name", "created_at", "updated_at")
