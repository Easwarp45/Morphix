from django.contrib import admin

from .models import Conversion


@admin.register(Conversion)
class ConversionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "conversion_type", "status", "processing_time", "created_at")
    list_filter = ("status", "conversion_type", "created_at")
    search_fields = ("user__email", "output_filename")
    readonly_fields = ("id", "celery_task_id", "created_at", "started_at", "completed_at")
