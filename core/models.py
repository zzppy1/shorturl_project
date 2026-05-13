from django.db import models

# Create your models here.

class ShortURL(models.Model):
    short_code = models.CharField(max_length=10, unique=True, db_index=True,null=True)
    original_url = models.URLField(max_length=2048)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    total_dicks = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.short_code} -> {self.original_url[:50]}"