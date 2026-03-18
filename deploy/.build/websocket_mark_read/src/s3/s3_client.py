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

if __name__ == "__main__":
    # ---- Test S3 Connection ----
    try:
        response = s3.list_buckets()
        print("✅ S3 Connection Successful!")
        print("Buckets I can access:", [b["Name"] for b in response["Buckets"]])
    except Exception as e:
        print("❌ S3 Connection Failed!")
        print(e)

    # ---- Test Upload and Delete ----
    def test_upload_and_delete():
        # Local imports to avoid circular dependency
        try:
            from upload import upload_file
            from delete import delete_file
        except ImportError:
            # Fallback for running directly from src/s3/
            from src.s3.upload import upload_file
            from src.s3.delete import delete_file
        
        print("\n---- Testing Upload and Delete ----")
        test_filename = "test_file.txt"
        test_content = b"Hello, S3!"
        
        print(f"Uploading {test_filename}...")
        upload_result = upload_file(test_content, test_filename)
        
        if upload_result["success"]:
            print(f"✅ Upload Successful! URL: {upload_result['url']}")
            file_key = upload_result["key"]
            
            print(f"Deleting {file_key}...")
            delete_result = delete_file(file_key)
            
            if delete_result["success"]:
                print("✅ Deletion Successful!")
            else:
                print(f"❌ Deletion Failed: {delete_result.get('error')}")
        else:
            print(f"❌ Upload Failed: {upload_result.get('error')}")

    test_upload_and_delete()