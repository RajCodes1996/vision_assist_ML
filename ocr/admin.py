from django.contrib import admin
from .models import ScanHistory

@admin.register(ScanHistory)
class ScanHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'mode', 'word_count', 'confidence', 'created_at']
    list_filter  = ['mode']
    search_fields = ['extracted_text']