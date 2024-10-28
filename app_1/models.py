import uuid
from django.db import models

class BGPTrafficTask(models.Model):
    TASK_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asn = models.IntegerField()
    target_prefixes = models.JSONField(null=True, blank=True)  # Requires PostgreSQL or Django 3.1+
    collection_period_minutes = models.FloatField(default=2.0)
    status = models.CharField(max_length=10, choices=TASK_STATUS_CHOICES, default='PENDING')
    media_dir = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"BGPTrafficTask {self.task_id} - ASN {self.asn}"