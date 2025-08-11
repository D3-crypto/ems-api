from django.conf import settings
from django.db import models


class Pandit(models.Model):
    Pandit_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    Location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pandits'
        unique_together = ['Pandit_name', 'Location']

    def __str__(self):
        return f"{self.Pandit_name} - {self.Location}"
