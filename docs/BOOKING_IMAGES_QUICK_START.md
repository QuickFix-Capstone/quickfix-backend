# Booking Images - Quick Start Guide

## TL;DR

Upload, view, and delete images for service bookings. Max 5 images per booking, 5MB each.

**Base URL:** `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com`

---

## 4 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/bookings/{id}/images/upload-url` | Get S3 upload URL |
| POST | `/bookings/{id}/images` | Save image metadata |
| GET | `/bookings/{id}/images` | Get all images |
| DELETE | `/bookings/{id}/images/{image_id}` | Delete image |

---

## Quick Upload Flow

```javascript
// 1. Get upload URL
const { upload_url, fields, image_key } = await fetch(
  `${API_BASE}/bookings/${bookingId}/images/upload-url`,
  {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({
      file_name: file.name,
      content_type: file.type,
      image_order: 1
    })
  }
).then(r => r.json());

// 2. Upload to S3
const formData = new FormData();
Object.entries(fields).forEach(([k, v]) => formData.append(k, v));
formData.append('file', file);
await fetch(upload_url, { method: 'POST', body: formData });

// 3. Save metadata
await fetch(`${API_BASE}/bookings/${bookingId}/images`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({
    image_key,
    image_order: 1,
    content_type: file.type,
    file_size: file.size
  })
});
```

---

## View Images

```javascript
const { images } = await fetch(
  `${API_BASE}/bookings/${bookingId}/images`,
  { headers: { 'Authorization': `Bearer ${token}` } }
).then(r => r.json());

// Display images
images.forEach(img => {
  console.log(img.url); // Presigned URL, expires in 1 hour
});
```

---

## Delete Image

```javascript
await fetch(
  `${API_BASE}/bookings/${bookingId}/images/${imageId}`,
  {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  }
);
```

---

## Key Points

✅ **Authentication:** All endpoints require Customer JWT token
✅ **Limits:** 5 images max per booking, 5MB per image
✅ **Formats:** JPEG, JPG, PNG, WebP only
✅ **Order:** Images have order 1-5, must be unique per booking
✅ **Presigned URLs:** View URLs expire in 1 hour, upload URLs in 5 minutes
✅ **Ownership:** Only booking owner can upload/delete images

---

## Common Errors

| Error | Meaning | Fix |
|-------|---------|-----|
| `Maximum 5 images per booking already reached` | Too many images | Delete one first |
| `image_order 1 is already used` | Order conflict | Use different number (1-5) |
| `Invalid content type` | Wrong file type | Use JPEG/PNG/WebP |
| `You do not have permission` | Not booking owner | Check booking ownership |
| `Image file not found in S3` | S3 upload failed | Retry upload to S3 first |

---

## Full Documentation

See [API_BOOKING_IMAGES.md](API_BOOKING_IMAGES.md) for complete details, error codes, and React examples.
