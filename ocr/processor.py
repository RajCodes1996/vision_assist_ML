import cv2
import numpy as np
import pytesseract
from PIL import Image
from django.conf import settings
import os

# Point pytesseract to the binary
pytesseract.pytesseract.tesseract_cmd = getattr(
    settings, 'TESSERACT_CMD', '/usr/bin/tesseract'
)


def preprocess_image(image_path: str) -> np.ndarray:
    """
    OpenCV preprocessing pipeline for better OCR accuracy.
    Steps: load → grayscale → denoise → threshold → deskew
    """
    # 1. Load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image at: {image_path}")

    # 2. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Denoise using Non-local Means (good for printed text)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # 4. Adaptive thresholding — handles uneven lighting in photos
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # 5. Deskew — straighten slightly rotated text
    deskewed = _deskew(thresh)

    return deskewed


def _deskew(image: np.ndarray) -> np.ndarray:
    """Detect and correct skew angle using image moments."""
    coords = np.column_stack(np.where(image > 0))
    if len(coords) < 10:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.5:   # skip tiny corrections
        return image
    h, w = image.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def run_ocr(image_path: str, mode: str = 'ocr') -> dict:
    """
    Main OCR function. Returns extracted text + metadata.

    Modes:
      'ocr'       — extract all text as-is
      'clean'     — extract and clean up whitespace/formatting
      'detailed'  — include per-word confidence scores
    """
    processed = preprocess_image(image_path)

    # Tesseract config: --oem 3 = LSTM engine, --psm 3 = auto page layout
    tess_config = '--oem 3 --psm 3'

    if mode == 'detailed':
        # Get bounding box + confidence data per word
        data = pytesseract.image_to_data(
            processed,
            config=tess_config,
            output_type=pytesseract.Output.DICT
        )
        words, confidences = [], []
        for i, word in enumerate(data['text']):
            conf = int(data['conf'][i])
            if conf > 40 and word.strip():
                words.append(word)
                confidences.append(conf)
        text = ' '.join(words)
        avg_conf = round(sum(confidences) / len(confidences), 1) if confidences else 0.0
    else:
        text = pytesseract.image_to_string(processed, config=tess_config)
        avg_conf = _estimate_confidence(processed)

    if mode == 'clean':
        text = _clean_text(text)

    word_count = len(text.split())

    return {
        'text': text.strip(),
        'word_count': word_count,
        'confidence': avg_conf,
        'mode': mode,
    }


def _estimate_confidence(image: np.ndarray) -> float:
    """Quick confidence estimate using Tesseract's mean score."""
    try:
        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT
        )
        confs = [int(c) for c in data['conf'] if str(c).lstrip('-').isdigit() and int(c) > 0]
        return round(sum(confs) / len(confs), 1) if confs else 0.0
    except Exception:
        return 0.0


def _clean_text(text: str) -> str:
    """Remove excessive whitespace and blank lines."""
    lines = [line.strip() for line in text.splitlines()]
    lines = [l for l in lines if l]
    return '\n'.join(lines)