import json
import os
import base64
from io import BytesIO
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from .models import ScanHistory
from .processor import run_ocr


def index(request):
    """Serve the main page."""
    history = ScanHistory.objects.all()[:10]
    return render(request, "ocr/index.html", {"history": history})


@csrf_exempt
@require_http_methods(["POST"])
def scan_image(request):
    """
    POST /scan/
    Accepts: multipart image file + mode field
    Returns: JSON with extracted text, confidence, word count
    """
    if "image" not in request.FILES:
        return JsonResponse({"error": "No image provided."}, status=400)

    image_file = request.FILES["image"]
    mode = request.POST.get("mode", "ocr")

    # Validate file type
    allowed = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}
    if image_file.content_type not in allowed:
        return JsonResponse({"error": "Unsupported file type."}, status=400)

    # Save temporarily
    saved_path = default_storage.save(f"uploads/{image_file.name}", image_file)
    abs_path = os.path.join(settings.MEDIA_ROOT, saved_path)

    try:
        result = run_ocr(abs_path, mode=mode)

        # Persist to DB
        scan = ScanHistory.objects.create(
            image=saved_path,
            extracted_text=result["text"],
            word_count=result["word_count"],
            confidence=result["confidence"],
            mode=mode,
        )

        return JsonResponse(
            {
                "success": True,
                "text": result["text"],
                "word_count": result["word_count"],
                "confidence": result["confidence"],
                "scan_id": scan.id,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    finally:
        # Clean up temp file
        if os.path.exists(abs_path):
            os.remove(abs_path)


@require_http_methods(["GET"])
def get_history(request):
    """GET /history/ — returns last 20 scans as JSON."""
    scans = ScanHistory.objects.all()[:20]
    data = [
        {
            "id": s.id,
            "text": s.extracted_text[:200],
            "word_count": s.word_count,
            "confidence": s.confidence,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for s in scans
    ]
    return JsonResponse({"history": data})


@csrf_exempt
@require_http_methods(["POST"])
def delete_history_item(request, scan_id):
    """POST /history/<id>/delete/ — deletes a saved scan and its image file."""
    scan = get_object_or_404(ScanHistory, pk=scan_id)

    if scan.image:
        try:
            scan.image.delete(save=False)
        except Exception:
            pass

    scan.delete()
    return JsonResponse({"success": True, "deleted_id": scan_id})


@csrf_exempt
@require_http_methods(["POST"])
def scan_base64(request):
    """
    POST /scan/base64/
    Accepts: JSON with base64 image data + mode field
    Returns: JSON with extracted text, confidence, word count
    Useful for programmatic access and hands-free operation
    """
    try:
        data = json.loads(request.body)
        base64_image = data.get("image")
        mode = data.get("mode", "ocr")

        if not base64_image:
            return JsonResponse({"error": "No image data provided."}, status=400)

        # Decode base64 image
        try:
            image_data = base64.b64decode(
                base64_image.split(",")[1]
            )  # Remove data:image/... prefix
            image_file = ContentFile(image_data, name="camera_capture.jpg")
        except Exception as e:
            return JsonResponse(
                {"error": f"Invalid base64 image data: {str(e)}"}, status=400
            )

        # Save temporarily
        saved_path = default_storage.save(
            f"uploads/camera_{image_file.name}", image_file
        )
        abs_path = os.path.join(settings.MEDIA_ROOT, saved_path)

        try:
            result = run_ocr(abs_path, mode=mode)

            # Persist to DB
            scan = ScanHistory.objects.create(
                image=saved_path,
                extracted_text=result["text"],
                word_count=result["word_count"],
                confidence=result["confidence"],
                mode=mode,
            )

            return JsonResponse(
                {
                    "success": True,
                    "text": result["text"],
                    "word_count": result["word_count"],
                    "confidence": result["confidence"],
                    "scan_id": scan.id,
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            # Clean up temp file
            if os.path.exists(abs_path):
                os.remove(abs_path)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data."}, status=400)


@require_http_methods(["GET"])
def voice_commands(request):
    """
    GET /voice-commands/
    Returns available voice commands for hands-free operation
    """
    commands = {
        "scan": "Take a photo and extract text",
        "camera": "Open camera for scanning",
        "history": "Read recent scans",
        "read latest": "Read the most recent scan aloud",
        "help": "List available voice commands",
    }
    return JsonResponse({"commands": commands})
