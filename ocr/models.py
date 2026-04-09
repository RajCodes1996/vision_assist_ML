from django.db import models

class ScanHistory(models.Model):
    image       = models.ImageField(upload_to='uploads/')
    extracted_text = models.TextField(blank=True)
    word_count  = models.IntegerField(default=0)
    confidence  = models.FloatField(default=0.0)
    mode        = models.CharField(max_length=20, default='ocr')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Scan {self.id} — {self.created_at:%Y-%m-%d %H:%M}"