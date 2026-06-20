from django.contrib import admin
from .models import AuditLog, Download


@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ("file_name", "user", "file_size", "downloaded_at")
    list_filter = ("downloaded_at",)
    search_fields = ("file_name", "user__email")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "resource_type", "ip_address", "created_at")
    list_filter = ("resource_type", "created_at")
    search_fields = ("action", "user__email")
    readonly_fields = ("id", "user", "action", "resource_type", "resource_id", "ip_address", "user_agent", "details", "created_at")
