from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone

User = get_user_model()

POST_TYPE_CHOICES = [
    ('government', 'Government'),
    ('publisher', 'Publisher'),
]

VC_STATUS_CHOICES = [
    ('issued', 'Issued'),
    ('revoked', 'Revoked'),
    ('pending', 'Pending'),
    ('invalid', 'Invalid'),
]

class Post(models.Model):
    """
    Unified table for all documents/posts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    # VC fields (for government documents or post issued as VC)
    vc_issuer_did = models.CharField(max_length=255, null=True, blank=True)
    vc_status = models.CharField(max_length=20, choices=VC_STATUS_CHOICES, default='pending')
    vc_proof = models.JSONField(default=dict, blank=True)  # Store Linked Data Proof or JWT
    vc_type = models.CharField(max_length=100, default="GovernmentPublicationCredential", blank=True, null=True)
    vc_issuance_date = models.DateTimeField(null=True, blank=True)
    vc_expiration_date = models.DateTimeField(null=True, blank=True)

    # Verification tracking
    proof = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.title} ({self.author.username})"
