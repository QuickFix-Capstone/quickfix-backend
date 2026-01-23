try:
    from .s3_client import s3, BUCKET
except ImportError:
    from s3_client import s3, BUCKET

def delete_file(key):
    try:
        s3.delete_object(Bucket=BUCKET, Key=key)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}