import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

BUCKET = os.getenv("S3_BUCKET")

# ---- Test S3 Connection ----
try:
    response = s3.list_buckets()
    print("✅ S3 Connection Successful!")
    print("Buckets I can access:", [b["Name"] for b in response["Buckets"]])
except Exception as e:
    print("❌ S3 Connection Failed!")
    print(e)