import boto3
import os
import uuid
import mimetypes
from datetime import timedelta

from shared.slugify import slugify


class S3Presigner:
    """
    Responsible for generating pre-signed S3 upload URLs
    for service offering images.
    """

    ALLOWED_CONTENT_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    def __init__(self):
        self.bucket_name = os.environ["CERT_BUCKET"]
        self.region = os.environ.get("AWS_REGION", "us-east-2")
        self.expiration = int(os.environ.get("URL_EXPIRATION_SECONDS", 600))

        self.s3_client = boto3.client("s3", region_name=self.region)

    def generate_upload_url(
        self,
        provider_id: str,
        service_title: str,
        content_type: str,
    ) -> dict:
        """
        Generates a pre-signed PUT URL for uploading an image to S3.

        Returns:
        {
            upload_url: str,
            s3_key: str,
            image_url: str
        }
        """

        # ------------------------------
        # 1️⃣ Validate content type
        # ------------------------------
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"Unsupported content type: {content_type}"
            )

        extension = self.ALLOWED_CONTENT_TYPES[content_type]

        # ------------------------------
        # 2️⃣ Build safe filename
        # ------------------------------
        slug = slugify(service_title)
        short_uuid = str(uuid.uuid4())[:8]

        filename = f"{provider_id}_{slug}_{short_uuid}{extension}"

        s3_key = f"service-offerings/{provider_id}/{filename}"

        # ------------------------------
        # 3️⃣ Generate pre-signed URL
        # ------------------------------
        upload_url = self.s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=self.expiration,
        )

        # ------------------------------
        # 4️⃣ Public image URL (stored in DB)
        # ------------------------------
        image_url = (
            f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
        )

        return {
            "upload_url": upload_url,
            "s3_key": s3_key,
            "image_url": image_url,
        }
