# Avatar Upload Feature - Setup Guide

## Overview

This guide explains how to set up and use the new avatar upload feature for customers.

## Architecture

The avatar upload feature uses a **presigned URL pattern** for secure, direct-to-S3 uploads:

1. **Client requests upload URL** → `POST /customers/avatar/upload`
2. **Lambda generates presigned URL** → Returns URL with 5-minute expiration
3. **Client uploads directly to S3** → No data passes through Lambda
4. **Client updates profile** → `PUT /customers/profile` with `avatar_url`

## Files Created/Modified

### New Files
- `lambda/customers/upload_avatar/handler.py` - Presigned URL generation Lambda
- `lambda/customers/upload_avatar/requirements.txt` - Dependencies (boto3)
- `deploy/deploy_upload_avatar.sh` - Deployment script
- `sql/migrations/add_avatar_url_to_customers.sql` - Database migration

### Modified Files
- `sql/quickfix-mysql.sql` - Added `avatar_url` column to schema
- `lambda/customers/update_customer/handler.py` - Added `avatar_url` support
- `lambda/customers/get_customer/handler.py` - Added `avatar_url` to response

## Setup Instructions

### 1. Database Migration

Run the migration script to add the `avatar_url` column:

```bash
mysql -h <your-host> -u <your-user> -p quickfix < sql/migrations/add_avatar_url_to_customers.sql
```

Or execute manually:
```sql
USE quickfix;
ALTER TABLE customers
ADD COLUMN avatar_url VARCHAR(512) NULL
COMMENT 'S3 URL for customer profile avatar';
```

### 2. S3 Bucket Setup

Create an S3 bucket for avatar storage (if not already exists):

```bash
aws s3 mb s3://quickfix-customer-avatars --region us-east-2
```

Configure CORS for the bucket to allow frontend uploads:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["PUT", "POST"],
    "AllowedOrigins": ["https://your-frontend-domain.com"],
    "ExposeHeaders": ["ETag"]
  }
]
```

Apply CORS configuration:
```bash
aws s3api put-bucket-cors \
  --bucket quickfix-customer-avatars \
  --cors-configuration file://cors-config.json
```

### 3. IAM Permissions

The Lambda execution role needs S3 permissions. Add this policy to your Lambda role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::quickfix-customer-avatars/avatars/*"
    }
  ]
}
```

### 4. Create Lambda Function

Create the `upload_avatar` Lambda function in AWS Console or via CLI:

```bash
aws lambda create-function \
  --function-name upload_avatar \
  --runtime python3.9 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler handler.handler \
  --zip-file fileb://placeholder.zip \
  --region us-east-2 \
  --environment Variables="{S3_BUCKET=quickfix-customer-avatars}"
```

### 5. Deploy Lambda Code

Deploy the upload_avatar Lambda:

```bash
cd deploy
./deploy_upload_avatar.sh
```

Redeploy existing customer Lambdas to include avatar_url changes:

```bash
./deploy_create_customer.sh
# Deploy update_customer and get_customer if you have scripts for them
```

### 6. API Gateway Configuration

Add a new route to your API Gateway:

- **Method**: POST
- **Path**: `/customers/avatar/upload`
- **Integration**: Lambda - `upload_avatar`
- **Authorization**: Cognito JWT Authorizer

## API Usage

### 1. Request Presigned URL

**Endpoint**: `POST /customers/avatar/upload`

**Headers**:
```
Authorization: Bearer <cognito-jwt-token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "file_name": "profile.jpg",
  "content_type": "image/jpeg"
}
```

**Response** (200 OK):
```json
{
  "message": "Presigned URL generated successfully",
  "upload_url": "https://quickfix-customer-avatars.s3.amazonaws.com/",
  "fields": {
    "key": "avatars/cognito-sub-123/20260101-141500-profile.jpg",
    "Content-Type": "image/jpeg",
    "policy": "...",
    "x-amz-algorithm": "AWS4-HMAC-SHA256",
    "x-amz-credential": "...",
    "x-amz-date": "...",
    "x-amz-signature": "..."
  },
  "avatar_url": "https://quickfix-customer-avatars.s3.amazonaws.com/avatars/cognito-sub-123/20260101-141500-profile.jpg",
  "expires_in": 300
}
```

### 2. Upload to S3

Use the presigned URL to upload directly from the browser:

```javascript
const formData = new FormData();

// Add all fields from the response
Object.entries(response.fields).forEach(([key, value]) => {
  formData.append(key, value);
});

// Add the file last
formData.append('file', fileBlob);

// Upload to S3
await fetch(response.upload_url, {
  method: 'POST',
  body: formData
});
```

### 3. Update Customer Profile

**Endpoint**: `PUT /customers/profile`

**Request Body**:
```json
{
  "avatar_url": "https://quickfix-customer-avatars.s3.amazonaws.com/avatars/cognito-sub-123/20260101-141500-profile.jpg"
}
```

**Response** (200 OK):
```json
{
  "message": "Customer updated successfully",
  "customer": {
    "customer_id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "avatar_url": "https://quickfix-customer-avatars.s3.amazonaws.com/avatars/..."
  }
}
```

## Validation Rules

- **Allowed file types**: JPEG, JPG, PNG, GIF, WebP
- **Max file size**: 5MB
- **URL expiration**: 5 minutes
- **File naming**: `avatars/{cognito_sub}/{timestamp}-{filename}`

## Security Considerations

1. **Authentication**: All endpoints require valid Cognito JWT
2. **File size limits**: Enforced at S3 level via presigned URL conditions
3. **File type validation**: Only image types allowed
4. **Unique paths**: Each user's avatars stored in their own S3 prefix
5. **URL expiration**: Presigned URLs expire after 5 minutes

## Testing

Test the upload_avatar Lambda locally:

```bash
cd lambda/customers/upload_avatar
python handler.py
```

Expected output:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Presigned URL generated successfully",
    "upload_url": "...",
    "fields": {...},
    "avatar_url": "...",
    "expires_in": 300
  }
}
```

## Troubleshooting

### Issue: "Access Denied" when uploading to S3
- Check Lambda IAM role has S3 permissions
- Verify bucket name in environment variable
- Check CORS configuration on S3 bucket

### Issue: "Invalid content type"
- Ensure `content_type` matches allowed types
- Check file extension matches content type

### Issue: Presigned URL expired
- URLs expire after 5 minutes
- Request a new URL if upload takes too long

## Environment Variables

The `upload_avatar` Lambda requires:

- `S3_BUCKET`: S3 bucket name (default: `quickfix-customer-avatars`)

Set via AWS Console or CLI:
```bash
aws lambda update-function-configuration \
  --function-name upload_avatar \
  --environment Variables="{S3_BUCKET=quickfix-customer-avatars}"
```
