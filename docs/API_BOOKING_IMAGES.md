# Booking Images API Documentation

## Overview

The Booking Images API allows customers to upload, view, and manage images (photos) for their service bookings. Customers can upload 1-5 images per booking to provide visual context (e.g., photos of issues that need fixing).

**Base URL:** `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com`

**Authentication:** All endpoints require JWT authentication (Cognito Customer token)

**Image Limits:**
- Maximum 5 images per booking
- Maximum 5MB per image
- Supported formats: JPEG, JPG, PNG, WebP

---

## Table of Contents

1. [Generate Upload URL](#1-generate-upload-url)
2. [Save Image Metadata](#2-save-image-metadata)
3. [Get Booking Images](#3-get-booking-images)
4. [Delete Booking Image](#4-delete-booking-image)
5. [Complete Workflow Example](#complete-workflow-example)
6. [Frontend Integration Code](#frontend-integration-code)

---

## API Endpoints

### 1. Generate Upload URL

**Purpose:** Get a presigned S3 URL for uploading an image file

**Endpoint:** `POST /bookings/{booking_id}/images/upload-url`

**Authentication:** Required (Customer JWT)

#### Request

**Path Parameters:**
- `booking_id` (required) - ID of the booking

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

**Body:**
```json
{
  "file_name": "kitchen_leak.jpg",
  "content_type": "image/jpeg",
  "image_order": 1
}
```

**Body Parameters:**

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `file_name` | string | Yes | Original file name | `"kitchen_leak.jpg"` |
| `content_type` | string | Yes | MIME type (must be image/*) | `"image/jpeg"` |
| `image_order` | number | Yes | Display order (1-5) | `1` |

**Validation:**
- `content_type` must be one of: `image/jpeg`, `image/jpg`, `image/png`, `image/webp`
- `image_order` must be between 1 and 5
- `image_order` must not be already used for this booking
- User must own the booking
- Booking cannot already have 5 images

#### Success Response (200 OK)

```json
{
  "message": "Presigned URL generated successfully",
  "upload_url": "https://quickfix-app-files.s3.amazonaws.com/",
  "fields": {
    "Content-Type": "image/jpeg",
    "key": "booking-images/75/20260126-233849-kitchen_leak.jpg",
    "x-amz-algorithm": "AWS4-HMAC-SHA256",
    "x-amz-credential": "...",
    "x-amz-date": "20260126T233849Z",
    "policy": "...",
    "x-amz-signature": "..."
  },
  "image_key": "booking-images/75/20260126-233849-kitchen_leak.jpg",
  "expires_in": 300
}
```

**Response Fields:**
- `upload_url` - S3 endpoint URL for uploading
- `fields` - Form fields to include in the upload request
- `image_key` - S3 key where the image will be stored (save this!)
- `expires_in` - Seconds until the URL expires (5 minutes)

#### Error Responses

**400 Bad Request**
```json
{
  "message": "Missing required field: file_name"
}
```
```json
{
  "message": "Invalid content type. Allowed types: image/jpeg, image/jpg, image/png, image/webp"
}
```
```json
{
  "message": "image_order must be between 1 and 5"
}
```
```json
{
  "message": "image_order 1 is already used for this booking"
}
```
```json
{
  "message": "Maximum 5 images per booking already reached"
}
```

**401 Unauthorized**
```json
{
  "message": "Unauthorized: Missing identity"
}
```

**403 Forbidden**
```json
{
  "message": "You do not have permission to upload images to this booking"
}
```

**404 Not Found**
```json
{
  "message": "Customer profile not found"
}
```

---

### 2. Save Image Metadata

**Purpose:** Save image metadata to database after uploading to S3

**Endpoint:** `POST /bookings/{booking_id}/images`

**Authentication:** Required (Customer JWT)

#### Request

**Path Parameters:**
- `booking_id` (required) - ID of the booking

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

**Body:**
```json
{
  "image_key": "booking-images/75/20260126-233849-kitchen_leak.jpg",
  "image_order": 1,
  "content_type": "image/jpeg",
  "file_size": 1048576,
  "description": "Water leak under kitchen sink"
}
```

**Body Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image_key` | string | Yes | S3 key from step 1 |
| `image_order` | number | Yes | Display order (1-5) |
| `content_type` | string | Yes | MIME type |
| `file_size` | number | Yes | File size in bytes |
| `description` | string | No | Image description (max 255 chars) |

**Validation:**
- S3 object must exist at `image_key`
- User must own the booking
- `image_order` must be available

#### Success Response (201 Created)

```json
{
  "message": "Image metadata saved successfully",
  "image": {
    "image_id": 123,
    "booking_id": 75,
    "image_key": "booking-images/75/20260126-233849-kitchen_leak.jpg",
    "image_order": 1,
    "content_type": "image/jpeg",
    "file_size": 1048576,
    "description": "Water leak under kitchen sink",
    "uploaded_by_id": 42,
    "created_at": "2026-01-26T23:38:49.000Z",
    "updated_at": "2026-01-26T23:38:49.000Z"
  }
}
```

#### Error Responses

**400 Bad Request**
```json
{
  "message": "Missing required fields",
  "missing": ["image_key", "file_size"]
}
```
```json
{
  "message": "Image file not found in S3. Please upload the file first."
}
```

**403 Forbidden**
```json
{
  "message": "You do not have permission to add images to this booking"
}
```

---

### 3. Get Booking Images

**Purpose:** Retrieve all images for a booking with presigned download URLs

**Endpoint:** `GET /bookings/{booking_id}/images`

**Authentication:** Required (Customer JWT)

#### Request

**Path Parameters:**
- `booking_id` (required) - ID of the booking

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
```

#### Success Response (200 OK)

```json
{
  "booking_id": 75,
  "images": [
    {
      "image_id": 123,
      "booking_id": 75,
      "image_key": "booking-images/75/20260126-233849-kitchen_leak.jpg",
      "image_order": 1,
      "content_type": "image/jpeg",
      "file_size": 1048576,
      "description": "Water leak under kitchen sink",
      "uploaded_by_id": 42,
      "created_at": "2026-01-26T23:38:49.000Z",
      "updated_at": "2026-01-26T23:38:49.000Z",
      "url": "https://quickfix-app-files.s3.amazonaws.com/booking-images/75/...?AWSAccessKeyId=...&Expires=...&Signature=..."
    },
    {
      "image_id": 124,
      "booking_id": 75,
      "image_key": "booking-images/75/20260126-234000-bathroom_pipe.jpg",
      "image_order": 2,
      "content_type": "image/jpeg",
      "file_size": 2048000,
      "description": "Leaking bathroom pipe",
      "uploaded_by_id": 42,
      "created_at": "2026-01-26T23:40:00.000Z",
      "updated_at": "2026-01-26T23:40:00.000Z",
      "url": "https://quickfix-app-files.s3.amazonaws.com/booking-images/75/...?AWSAccessKeyId=...&Expires=...&Signature=..."
    }
  ],
  "count": 2
}
```

**Response Fields:**
- `booking_id` - ID of the booking
- `images` - Array of image objects (sorted by `image_order`)
- `count` - Total number of images
- `url` - Presigned URL for viewing/downloading (expires in 1 hour)

#### Error Responses

**403 Forbidden**
```json
{
  "message": "You do not have permission to view images for this booking"
}
```

**404 Not Found**
```json
{
  "message": "Customer profile not found"
}
```

---

### 4. Delete Booking Image

**Purpose:** Delete an image from both S3 and database

**Endpoint:** `DELETE /bookings/{booking_id}/images/{image_id}`

**Authentication:** Required (Customer JWT)

#### Request

**Path Parameters:**
- `booking_id` (required) - ID of the booking
- `image_id` (required) - ID of the image to delete

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
```

#### Success Response (200 OK)

```json
{
  "message": "Image deleted successfully",
  "image_id": 123,
  "booking_id": 75
}
```

#### Error Responses

**403 Forbidden**
```json
{
  "message": "You do not have permission to delete images from this booking"
}
```

**404 Not Found**
```json
{
  "message": "Image not found"
}
```
```json
{
  "message": "Image not found for this booking"
}
```

---

## Complete Workflow Example

### Uploading an Image

```
1. Customer selects image file
   ↓
2. Frontend calls: POST /bookings/75/images/upload-url
   → Gets presigned URL + image_key
   ↓
3. Frontend uploads file directly to S3 using presigned URL
   ↓
4. Frontend calls: POST /bookings/75/images
   → Saves metadata to database with image_key
   ↓
5. Done! Image is now associated with booking
```

### Viewing Images

```
1. Frontend calls: GET /bookings/75/images
   ↓
2. Backend returns array of images with presigned download URLs
   ↓
3. Frontend displays images using the URLs
```

### Deleting an Image

```
1. User clicks delete on image
   ↓
2. Frontend calls: DELETE /bookings/75/images/123
   ↓
3. Backend deletes from S3 and database
   ↓
4. Frontend refreshes image list
```

---

## Frontend Integration Code

### React/TypeScript Example

```typescript
import { fetchAuthSession } from "aws-amplify/auth";

const API_BASE = "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com";

// Helper: Get JWT token
async function getAuthToken(): Promise<string> {
  const { tokens } = await fetchAuthSession();
  return tokens.idToken.toString();
}

// 1. Upload a booking image
export async function uploadBookingImage(
  bookingId: number,
  file: File,
  imageOrder: number,
  description?: string
): Promise<void> {
  const token = await getAuthToken();

  // Step 1: Get presigned URL
  const urlResponse = await fetch(
    `${API_BASE}/bookings/${bookingId}/images/upload-url`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        file_name: file.name,
        content_type: file.type,
        image_order: imageOrder
      })
    }
  );

  if (!urlResponse.ok) {
    const error = await urlResponse.json();
    throw new Error(error.message || "Failed to get upload URL");
  }

  const { upload_url, fields, image_key } = await urlResponse.json();

  // Step 2: Upload file to S3
  const formData = new FormData();
  Object.entries(fields).forEach(([key, value]) => {
    formData.append(key, value as string);
  });
  formData.append("file", file);

  const uploadResponse = await fetch(upload_url, {
    method: "POST",
    body: formData
  });

  if (!uploadResponse.ok) {
    throw new Error("Failed to upload image to S3");
  }

  // Step 3: Save metadata
  const metadataResponse = await fetch(
    `${API_BASE}/bookings/${bookingId}/images`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        image_key,
        image_order: imageOrder,
        content_type: file.type,
        file_size: file.size,
        description: description || null
      })
    }
  );

  if (!metadataResponse.ok) {
    const error = await metadataResponse.json();
    throw new Error(error.message || "Failed to save image metadata");
  }
}

// 2. Get all images for a booking
export async function getBookingImages(bookingId: number) {
  const token = await getAuthToken();

  const response = await fetch(
    `${API_BASE}/bookings/${bookingId}/images`,
    {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || "Failed to fetch images");
  }

  return await response.json();
}

// 3. Delete an image
export async function deleteBookingImage(
  bookingId: number,
  imageId: number
): Promise<void> {
  const token = await getAuthToken();

  const response = await fetch(
    `${API_BASE}/bookings/${bookingId}/images/${imageId}`,
    {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || "Failed to delete image");
  }
}
```

### React Component Example

```tsx
import React, { useState, useEffect } from 'react';
import { uploadBookingImage, getBookingImages, deleteBookingImage } from './api/bookings';

interface BookingImage {
  image_id: number;
  image_order: number;
  url: string;
  description: string;
  content_type: string;
  file_size: number;
}

export function BookingImageUploader({ bookingId }: { bookingId: number }) {
  const [images, setImages] = useState<BookingImage[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load existing images
  useEffect(() => {
    loadImages();
  }, [bookingId]);

  async function loadImages() {
    try {
      const data = await getBookingImages(bookingId);
      setImages(data.images);
    } catch (err) {
      console.error("Failed to load images:", err);
    }
  }

  // Handle file upload
  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      setError('Image must be less than 5MB');
      return;
    }

    // Check image limit
    if (images.length >= 5) {
      setError('Maximum 5 images per booking');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const nextOrder = images.length + 1;
      await uploadBookingImage(bookingId, file, nextOrder);
      await loadImages(); // Refresh list
      e.target.value = ''; // Clear input
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  // Handle image deletion
  async function handleDelete(imageId: number) {
    if (!confirm('Delete this image?')) return;

    try {
      await deleteBookingImage(bookingId, imageId);
      await loadImages(); // Refresh list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  }

  return (
    <div className="booking-image-uploader">
      <h3>Booking Photos ({images.length}/5)</h3>

      {error && <div className="error">{error}</div>}

      {/* Upload button */}
      <div className="upload-section">
        <input
          type="file"
          accept="image/jpeg,image/jpg,image/png,image/webp"
          onChange={handleFileUpload}
          disabled={uploading || images.length >= 5}
          style={{ display: 'none' }}
          id="image-upload"
        />
        <label htmlFor="image-upload">
          <button
            type="button"
            disabled={uploading || images.length >= 5}
            onClick={() => document.getElementById('image-upload')?.click()}
          >
            {uploading ? 'Uploading...' : 'Add Photo'}
          </button>
        </label>
      </div>

      {/* Image gallery */}
      <div className="image-gallery">
        {images.map((image) => (
          <div key={image.image_id} className="image-item">
            <img src={image.url} alt={image.description || `Image ${image.image_order}`} />
            <div className="image-info">
              <p>{image.description}</p>
              <button onClick={() => handleDelete(image.image_id)}>
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Error Handling Best Practices

### 1. Validate before API calls
```typescript
// Check file type
const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
if (!validTypes.includes(file.type)) {
  throw new Error('Invalid file type');
}

// Check file size
if (file.size > 5 * 1024 * 1024) {
  throw new Error('File too large (max 5MB)');
}

// Check image count
if (currentImages.length >= 5) {
  throw new Error('Maximum 5 images allowed');
}
```

### 2. Handle network errors
```typescript
try {
  await uploadBookingImage(bookingId, file, order);
} catch (error) {
  if (error.message.includes('Network')) {
    // Show network error message
  } else if (error.message.includes('permission')) {
    // Show permission error
  } else {
    // Show generic error
  }
}
```

### 3. Retry S3 uploads on failure
```typescript
async function uploadWithRetry(url: string, formData: FormData, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, { method: 'POST', body: formData });
      if (response.ok) return;
    } catch (err) {
      if (i === maxRetries - 1) throw err;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

---

## Testing

### Using cURL

**1. Get upload URL:**
```bash
curl -X POST \
  "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/bookings/75/images/upload-url" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "test.jpg",
    "content_type": "image/jpeg",
    "image_order": 1
  }'
```

**2. Upload to S3:**
```bash
# Use the fields returned from step 1
curl -X POST \
  "https://quickfix-app-files.s3.amazonaws.com/" \
  -F "key=booking-images/75/..." \
  -F "Content-Type=image/jpeg" \
  -F "x-amz-algorithm=AWS4-HMAC-SHA256" \
  -F "x-amz-credential=..." \
  -F "x-amz-date=..." \
  -F "policy=..." \
  -F "x-amz-signature=..." \
  -F "file=@/path/to/image.jpg"
```

**3. Save metadata:**
```bash
curl -X POST \
  "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/bookings/75/images" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_key": "booking-images/75/...",
    "image_order": 1,
    "content_type": "image/jpeg",
    "file_size": 1048576
  }'
```

**4. Get images:**
```bash
curl -X GET \
  "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/bookings/75/images" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**5. Delete image:**
```bash
curl -X DELETE \
  "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/bookings/75/images/123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Support

For questions or issues with the Booking Images API:
- Check the [Create Booking API Documentation](API_CREATE_BOOKING.md)
- Review backend logs in CloudWatch
- Contact the backend team

---

## Changelog

**2026-01-26:**
- Initial release
- Added 4 endpoints for booking image management
- Support for up to 5 images per booking
- Presigned URL-based upload for security
