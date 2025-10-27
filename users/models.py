from enum import Enum
from django.db import models
from django.contrib.auth.models import User

class UserType(Enum):
    ADMIN = 'ADMIN'
    MINISTRY = 'MINISTRY'
    PUBLISHER = 'PUBLISHER'
    USER = 'USER'

    @classmethod
    def choices(cls):
        # Returns list of tuples (value, display_name)
        return [(choice.value, choice.value) for choice in cls]  # key = value

# UserProfile model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    did_url = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices(),
        default=UserType.USER.value
    )
    user_profile = models.URLField(blank=True, null=True)
    org_name = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"



class DIDKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # optional owner
    did = models.CharField(max_length=255, unique=True)
    private_key_b64 = models.TextField()  # store the private key securely (Base64)
    public_key_b64 = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.did