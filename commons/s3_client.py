import boto3
from django.conf import settings
import mimetypes
import json


class S3Client:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

    def upload_json(self, key: str, data: dict):
        """Uploads a JSON object to S3."""
        json_bytes = json.dumps(data, indent=2).encode("utf-8")
        content_type = mimetypes.guess_type(key)[0] or "application/json"

        self.s3_client.put_object(
            Bucket=settings.AWS_DID_DOCUMENT_BUCKET_NAME,
            Key=key,
            Body=json_bytes,
            ContentType=content_type,
        )

        return f"https://{settings.AWS_DID_DOCUMENT_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"
