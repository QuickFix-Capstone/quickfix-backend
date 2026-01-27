# Booking Images API - Frontend Integration Guide

## Overview

Uploading booking images requires **TWO API calls**:

1. **Get Presigned Upload URL** - Get temporary S3 upload credentials
2. **Upload to S3** - Client uploads file directly to S3
3. **Create Database Record** - Save image metadata

Retrieving images requires **ONE API call**:
- **Get Images** - Returns images with temporary viewing URLs

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ UPLOAD FLOW (3 Steps)                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. POST /bookings/{booking_id}/images/upload               │
│     Headers: Authorization: Bearer <JWT>                    │
│     Body: { file_name, content_type, image_order }          │
│     Response: { upload_url, fields, image_key }             │
│                                                              │
│  2. POST to upload_url (S3)                                 │
│     Multipart form-data with fields + file                  │
│     Response: 204 No Content (success)                      │
│                                                              │
│  3. POST /bookings/{booking_id}/images                      │
│     Headers: Authorization: Bearer <JWT>                    │
│     Body: { image_key, image_order, content_type, ... }     │
│     Response: { image_id, booking_id, image_order }         │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ RETRIEVE FLOW (1 Step)                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GET /bookings/{booking_id}/images                          │
│  Headers: Authorization: Bearer <JWT>                       │
│  Response: { booking_id, images: [...], count }             │
│  Each image includes a temporary 'url' for viewing          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## API Reference

### 1. Get Presigned Upload URL

**Endpoint:** `POST /bookings/{booking_id}/images/upload`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Request Body:**
```json
{
  "file_name": "kitchen_photo.jpg",
  "content_type": "image/jpeg",
  "image_order": 1
}
```

**Validation Rules:**
- `file_name`: Required, string
- `content_type`: Required, must be: `image/jpeg`, `image/jpg`, `image/png`, or `image/webp`
- `image_order`: Required, integer 1-5, must not already be used for this booking
- Max 5 images per booking
- Max file size: 5MB

**Success Response (200):**
```json
{
  "message": "Presigned URL generated successfully",
  "upload_url": "https://quickfix-app-files.s3.amazonaws.com/",
  "fields": {
    "Content-Type": "image/jpeg",
    "key": "booking-images/75/20260127-033715-kitchen_photo.jpg",
    "x-amz-algorithm": "AWS4-HMAC-SHA256",
    "x-amz-credential": "...",
    "x-amz-date": "...",
    "policy": "...",
    "x-amz-signature": "..."
  },
  "image_key": "booking-images/75/20260127-033715-kitchen_photo.jpg",
  "expires_in": 300
}
```

**Error Responses:**
- `400`: Invalid input, max images exceeded, or image_order already used
- `401`: Missing or invalid JWT
- `403`: Not the booking owner
- `404`: Booking or customer not found

---

### 2. Upload File to S3

**Endpoint:** `POST <upload_url>` (from step 1 response)

**Content-Type:** `multipart/form-data`

**Form Data:**
1. Include ALL fields from step 1 response
2. Add the file as the last field

**JavaScript Example:**
```javascript
const formData = new FormData();

// Add all fields from the presigned POST response
Object.keys(response.fields).forEach(key => {
  formData.append(key, response.fields[key]);
});

// Add the file last
formData.append('file', file);

// Upload to S3
const uploadResponse = await fetch(response.upload_url, {
  method: 'POST',
  body: formData
});

if (uploadResponse.status === 204) {
  console.log('Upload successful!');
}
```

**Success Response:** `204 No Content`

**Error Responses:**
- `400`: Invalid file size or content type
- `403`: Expired or invalid signature

---

### 3. Create Database Record

**Endpoint:** `POST /bookings/{booking_id}/images`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Request Body:**
```json
{
  "image_key": "booking-images/75/20260127-033715-kitchen_photo.jpg",
  "image_order": 1,
  "content_type": "image/jpeg",
  "file_size": 1024500,
  "description": "Kitchen before repair (optional)"
}
```

**Field Notes:**
- `image_key`: Use the value from step 1 response
- `file_size`: Actual file size in bytes
- `description`: Optional field

**Success Response (200):**
```json
{
  "message": "Image metadata saved successfully",
  "image_id": 6,
  "booking_id": 75,
  "image_order": 1
}
```

**Error Responses:**
- `400`: S3 object not found (must upload to S3 first!)
- `401`: Missing or invalid JWT
- `403`: Not the booking owner
- `404`: Booking or customer not found

---

### 4. Get Booking Images

**Endpoint:** `GET /bookings/{booking_id}/images`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Success Response (200):**
```json
{
  "booking_id": 75,
  "images": [
    {
      "image_id": 4,
      "image_key": "booking-images/75/20260127-012308-test-image.jpg",
      "image_order": 1,
      "content_type": "image/jpeg",
      "file_size": 8229,
      "description": "Kitchen before repair",
      "uploaded_by_id": 12,
      "created_at": "2026-01-27T01:23:10",
      "url": "https://quickfix-app-files.s3.amazonaws.com/booking-images/75/...?X-Amz-Algorithm=..."
    }
  ],
  "count": 1
}
```

**Notes:**
- The `url` field is a **temporary presigned URL** that expires in 1 hour
- Always use the latest URL from this API call for viewing images
- Images are sorted by `image_order`

---

## Complete JavaScript Example

```javascript
async function uploadBookingImage(bookingId, file, imageOrder, description = '') {
  try {
    // Step 1: Get presigned URL
    const step1Response = await fetch(
      `/bookings/${bookingId}/images/upload`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getJwtToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file_name: file.name,
          content_type: file.type,
          image_order: imageOrder
        })
      }
    );

    if (!step1Response.ok) {
      const error = await step1Response.json();
      throw new Error(error.message);
    }

    const { upload_url, fields, image_key } = await step1Response.json();
    console.log('✅ Step 1: Got presigned URL');

    // Step 2: Upload to S3
    const formData = new FormData();
    Object.keys(fields).forEach(key => {
      formData.append(key, fields[key]);
    });
    formData.append('file', file);

    const step2Response = await fetch(upload_url, {
      method: 'POST',
      body: formData
    });

    if (!step2Response.ok) {
      throw new Error('S3 upload failed');
    }
    console.log('✅ Step 2: Uploaded to S3');

    // Step 3: Create database record
    const step3Response = await fetch(
      `/bookings/${bookingId}/images`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getJwtToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image_key: image_key,
          image_order: imageOrder,
          content_type: file.type,
          file_size: file.size,
          description: description
        })
      }
    );

    if (!step3Response.ok) {
      const error = await step3Response.json();
      throw new Error(error.message);
    }

    const result = await step3Response.json();
    console.log('✅ Step 3: Saved to database', result);

    return result;

  } catch (error) {
    console.error('❌ Upload failed:', error.message);
    throw error;
  }
}

async function getBookingImages(bookingId) {
  const response = await fetch(
    `/bookings/${bookingId}/images`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${getJwtToken()}`
      }
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message);
  }

  const data = await response.json();
  return data.images; // Array of images with temporary URLs
}
```

---

## Common Issues & Debugging

### ❌ "image_order X is already used for this booking"
**Cause:** That image order slot is taken.
**Solution:** Check existing images first or let user choose a different order.

```javascript
// Get current images to find available orders
const { images } = await getBookingImages(bookingId);
const usedOrders = images.map(img => img.image_order);
const availableOrders = [1, 2, 3, 4, 5].filter(o => !usedOrders.includes(o));
```

### ❌ "Maximum 5 images per booking already reached"
**Cause:** Booking already has 5 images.
**Solution:** User must delete an existing image before uploading a new one.

### ❌ "Image not found in S3. Please upload the image first using the upload URL"
**Cause:** Step 2 (S3 upload) failed or was skipped.
**Solution:** Ensure S3 upload returns 204 before calling step 3.

### ❌ "403 Forbidden"
**Cause:** User doesn't own this booking.
**Solution:** Verify the JWT token belongs to the booking's customer.

### ❌ "Invalid content type"
**Cause:** File type not allowed.
**Solution:** Only allow: JPEG, JPG, PNG, WEBP. Check `file.type` before upload.

### ❌ Upload returns 400 from S3
**Cause:** File exceeds 5MB or wrong content type.
**Solution:** Validate file size on frontend before starting upload.

```javascript
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];

if (file.size > MAX_FILE_SIZE) {
  alert('File too large. Max size is 5MB');
  return;
}

if (!ALLOWED_TYPES.includes(file.type)) {
  alert('Invalid file type. Only JPEG, PNG, and WEBP allowed');
  return;
}
```

---

## Testing with cURL

```bash
# Step 1: Get presigned URL
curl -X POST https://api.quickfix.com/bookings/75/images/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "test.jpg",
    "content_type": "image/jpeg",
    "image_order": 1
  }'

# Step 2: Upload to S3 (save fields from step 1 response)
curl -X POST "UPLOAD_URL_FROM_STEP_1" \
  -F "Content-Type=image/jpeg" \
  -F "key=IMAGE_KEY_FROM_STEP_1" \
  -F "x-amz-algorithm=VALUE_FROM_FIELDS" \
  -F "x-amz-credential=VALUE_FROM_FIELDS" \
  -F "x-amz-date=VALUE_FROM_FIELDS" \
  -F "policy=VALUE_FROM_FIELDS" \
  -F "x-amz-signature=VALUE_FROM_FIELDS" \
  -F "file=@/path/to/test.jpg"

# Step 3: Create database record
curl -X POST https://api.quickfix.com/bookings/75/images \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_key": "IMAGE_KEY_FROM_STEP_1",
    "image_order": 1,
    "content_type": "image/jpeg",
    "file_size": 123456,
    "description": "Test image"
  }'

# Get images
curl -X GET https://api.quickfix.com/bookings/75/images \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Important Notes

1. **URLs Expire:**
   - Upload URLs expire in **5 minutes**
   - Viewing URLs expire in **1 hour**
   - Always get fresh URLs when needed

2. **Data Storage:**
   - Database stores: S3 key/path (permanent)
   - Client receives: Presigned URLs (temporary)

3. **Image Orders:**
   - Must be unique per booking (1-5)
   - Frontend should track which orders are used
   - Users can choose any available order

4. **File Validation:**
   - Do validation on frontend before starting upload
   - Backend also validates for security

5. **Error Handling:**
   - Always check response status codes
   - Show user-friendly error messages
   - Log detailed errors for debugging

---

## Support

For issues or questions, check:
- API logs in CloudWatch
- Database records in `booking_images` table
- S3 bucket: `quickfix-app-files`
- Prefix: `booking-images/{booking_id}/`
