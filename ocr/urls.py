from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("scan/", views.scan_image, name="scan"),
    path("scan/base64/", views.scan_base64, name="scan_base64"),
    path("history/", views.get_history, name="history"),
    path("history/<int:scan_id>/delete/", views.delete_history_item, name="delete_history_item"),
    path("voice-commands/", views.voice_commands, name="voice_commands"),
]
