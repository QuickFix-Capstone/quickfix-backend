import uuid
from .s3_client import s3, BUCKET

def upload_file(file_bytes, filename, folder="uploads"):
    key = f"{folder}/{uuid.uuid4()}_{filename}"

    try:
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=file_bytes
        )

        return {
            "success": True,
            "url": f"https://{BUCKET}.s3.amazonaws.com/{key}",
            "key": key
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

