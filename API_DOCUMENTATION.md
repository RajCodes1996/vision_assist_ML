# Vision Assist API Documentation

## Overview
Vision Assist provides both web interface and API access for hands-free OCR operations, specifically designed for blind and low-vision users.

## Web Interface Features
- Voice command recognition ("scan", "camera", "history", "read latest", "help")
- Keyboard shortcuts (Alt+V for voice, Alt+R to read, Alt+S to scan)
- Automatic camera capture with speech feedback
- Text-to-speech output for all extracted text

## API Endpoints

### POST /scan/base64/
Accepts base64-encoded images for programmatic OCR processing.

**Request Body (JSON):**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
  "mode": "ocr"  // optional: "ocr", "clean", or "detailed"
}
```

**Response:**
```json
{
  "success": true,
  "text": "Extracted text content...",
  "word_count": 42,
  "confidence": 87.5,
  "scan_id": 123
}
```

### GET /voice-commands/
Returns available voice commands.

**Response:**
```json
{
  "commands": {
    "scan": "Take a photo and extract text",
    "camera": "Open camera for scanning",
    "history": "Read recent scans",
    "read latest": "Read the most recent scan aloud",
    "help": "List available voice commands"
  }
}
```

## Hands-Free Usage Examples

### Using Voice Commands
1. Click the microphone button (🎤) or press Alt+V
2. Say "scan" to open camera and capture an image
3. Say "read latest" to hear the extracted text

### Programmatic Access
```javascript
// Capture image from camera and send to API
async function scanWithAPI(imageBlob) {
  const base64 = await blobToBase64(imageBlob);
  const response = await fetch('/scan/base64/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: base64 })
  });
  const result = await response.json();
  speakText(result.text);
}
```

### Mobile App Integration
External apps can send images directly to the API without user interaction:
- Camera apps can POST base64 images
- Screen readers can trigger scans programmatically
- Smart home devices can send captured images

## Accessibility Features
- All operations work without visual feedback
- Speech synthesis provides audio confirmation
- Keyboard navigation for all functions
- Screen reader compatible
- Works offline for core functionality</content>
<parameter name="filePath">c:\Users\netware\Desktop\blind\vision_assist\API_DOCUMENTATION.md