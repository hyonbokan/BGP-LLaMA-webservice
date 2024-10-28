import uuid
from django.db import models

class BGPTrafficTask(models.Model):
    TASK_STATUS_CHOICES = [
        ('STARTED', 'Started'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('GENERATING', 'Generating RAG Query Results'),
        ('RAG_COMPLETED', 'RAG Query Completed'),
    ]

    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=40, null=True, blank=True)
    query = models.TextField()
    asn = models.CharField(max_length=20)
    target_prefixes = models.JSONField(null=True, blank=True)
    collection_period_minutes = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='STARTED')
    media_dir = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)