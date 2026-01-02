# S3 Bucket Policy Setup for Avatar Public Access

## Overview

To make customer avatars publicly accessible, you need to configure an S3 bucket policy instead of using ACLs on individual objects.

## Why Bucket Policy Instead of ACL?

✅ **Centralized control** - One policy for all avatars  
✅ **Easier to manage** - No need to set ACL on each upload  
✅ **More secure** - Can restrict by path prefix  
✅ **Better practice** - AWS recommends bucket policies over ACLs

## Step-by-Step Setup

### 1. Go to S3 Console

Navigate to: https://s3.console.aws.amazon.com/s3/buckets/quickfix-app-files

### 2. Configure Bucket Policy

1. Click on the **"Permissions"** tab
2. Scroll down to **"Bucket policy"**
3. Click **"Edit"**
4. Paste the policy from `s3-bucket-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadCustomerAvatars",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::quickfix-app-files/customers-avatar/*"
    }
  ]
}
```

5. Click **"Save changes"**

### 3. Verify Public Access Settings

Make sure **"Block all public access"** is configured to allow this policy:

1. In the **"Permissions"** tab
2. Under **"Block public access (bucket settings)"**
3. Click **"Edit"**
4. **Uncheck** "Block all public access" OR
5. **Uncheck** only "Block public access to buckets and objects granted through new public bucket or access point policies"
6. Click **"Save changes"**
7. Type `confirm` when prompted

## What This Policy Does

- **Allows**: Public read access (`s3:GetObject`)
- **Only for**: Files in `customers-avatar/*` folder
- **Does NOT affect**: Other folders like `certifications/` or `message-attachments/`

## Security Notes

✅ **Safe** - Only avatar images are public  
✅ **Scoped** - Limited to `customers-avatar/` prefix  
✅ **Read-only** - Users cannot upload, delete, or list objects  
✅ **No authentication needed** - Anyone can view avatar URLs

## Testing

After applying the policy:

1. Upload an avatar via the API
2. Get the `avatar_url` from the response
3. Open the URL in a browser (incognito mode)
4. The image should display without authentication

Example URL:
```
https://quickfix-app-files.s3.amazonaws.com/customers-avatar/415b3510-a0a1-7d8e-6a02-dc457aec9ecc/20260101-201616-avatar.png
```

## Alternative: Using AWS CLI

You can also apply the policy using AWS CLI:

```bash
aws s3api put-bucket-policy \
  --bucket quickfix-app-files \
  --policy file://docs/s3-bucket-policy.json
```

## Troubleshooting

### Error: "Access Denied" when viewing avatar
- Check bucket policy is applied correctly
- Verify "Block public access" settings allow the policy
- Ensure the file path starts with `customers-avatar/`

### Error: "The bucket does not allow ACLs"
- This is expected - we're using bucket policy, not ACLs
- No action needed

### Policy conflicts with existing policies
- If you have existing bucket policies, merge them
- Add the new statement to the existing policy's `Statement` array

## Current Status

✅ **Handler updated** - No ACL in presigned POST  
⏳ **Bucket policy** - Needs to be applied manually  
⏳ **Public access** - Will work after policy is applied
