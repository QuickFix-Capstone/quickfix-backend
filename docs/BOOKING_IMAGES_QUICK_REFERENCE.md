# Booking Images API - Quick Reference

## 🚀 Quick Start (3 Steps)

### Step 1: Get Upload URL
```http
POST /bookings/{booking_id}/images/upload
Authorization: Bearer {JWT}

{
  "file_name": "photo.jpg",
  "content_type": "image/jpeg",
  "image_order": 1
}

→ Returns: { upload_url, fields, image_key }
```

### Step 2: Upload to S3
```javascript
const form = new FormData();
Object.keys(response.fields).forEach(k => form.append(k, response.fields[k]));
form.append('file', fileObject);
await fetch(response.upload_url, { method: 'POST', body: form });
```

### Step 3: Save Metadata
```http
POST /bookings/{booking_id}/images
Authorization: Bearer {JWT}

{
  "image_key": "{from step 1}",
  "image_order": 1,
  "content_type": "image/jpeg",
  "file_size": 123456
}

→ Returns: { image_id, booking_id, image_order }
```

---

## 📥 Retrieve Images

```http
GET /bookings/{booking_id}/images
Authorization: Bearer {JWT}

→ Returns: { images: [...], count }
```

Each image has a temporary `url` field for viewing (expires in 1 hour).

---

## ⚠️ Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `400: image_order already used` | Order 1-5 already taken | Use different order or delete existing image |
| `400: Maximum 5 images` | Booking has 5 images | Delete an image first |
| `400: Image not found in S3` | Step 2 (S3 upload) failed | Verify S3 upload returns 204 |
| `403: Forbidden` | Not booking owner | Check JWT matches booking's customer |
| `400: Invalid content type` | Wrong file type | Only: jpeg, jpg, png, webp |
| S3 returns 400 | File > 5MB | Validate size on frontend |

---

## 🔍 Debug Checklist

- [ ] JWT token is valid and from correct user
- [ ] File type is: `image/jpeg`, `image/jpg`, `image/png`, or `image/webp`
- [ ] File size ≤ 5MB
- [ ] Image order 1-5 is not already used
- [ ] Booking has < 5 images
- [ ] S3 upload returns 204 before step 3
- [ ] Using `image_key` from step 1 in step 3
- [ ] All fields from step 1 included in S3 upload

---

## 📋 Validation Rules

| Field | Rule |
|-------|------|
| `file_name` | Required, string |
| `content_type` | Required, must be: `image/jpeg`, `image/jpg`, `image/png`, `image/webp` |
| `image_order` | Required, integer 1-5, unique per booking |
| `file_size` | Max 5MB (5,242,880 bytes) |
| Max images | 5 per booking |
| URL expiry | Upload: 5min, View: 1hr |

---

## 💾 What's Stored Where

| Data | Location | Persistent? |
|------|----------|-------------|
| Image file | S3: `quickfix-app-files` | Yes |
| S3 key/path | Database: `booking_images.image_key` | Yes |
| Upload URL | Response only | No (expires 5min) |
| Viewing URL | Generated on-demand | No (expires 1hr) |

**Important:** Database stores the **S3 key** (permanent), not URLs (temporary).

Example S3 key: `booking-images/75/20260127-033715-photo.jpg`

---

## 🧪 Test Locally

```bash
# Run the complete flow test
python3 /path/to/test_full_upload_flow.py

# Or test individual handlers
python3 lambda/bookings/upload_booking_image/handler.py
python3 lambda/bookings/create_booking_image/handler.py
python3 lambda/bookings/get_booking_images/handler.py
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE booking_images (
  image_id INT PRIMARY KEY AUTO_INCREMENT,
  booking_id INT NOT NULL,
  image_key VARCHAR(512) NOT NULL,        -- S3 path
  image_order TINYINT NOT NULL,           -- 1-5
  content_type VARCHAR(50),
  file_size INT,
  description TEXT,
  uploaded_by_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY (booking_id, image_order),
  FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
  FOREIGN KEY (uploaded_by_id) REFERENCES customers(customer_id)
);
```

---

## 🔗 API Endpoints Summary

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/bookings/{id}/images/upload` | Get presigned upload URL | JWT ✅ |
| POST | S3 upload URL | Upload file to S3 | Presigned ✅ |
| POST | `/bookings/{id}/images` | Save image metadata | JWT ✅ |
| GET | `/bookings/{id}/images` | Get images with URLs | JWT ✅ |
| DELETE | `/bookings/{id}/images/{image_id}` | Delete image | JWT ✅ |

---

## 📱 Frontend Code Snippet

```javascript
// Upload image
async function upload(bookingId, file, order) {
  // 1. Get URL
  const r1 = await fetch(`/bookings/${bookingId}/images/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      file_name: file.name,
      content_type: file.type,
      image_order: order
    })
  });
  const { upload_url, fields, image_key } = await r1.json();

  // 2. Upload to S3
  const form = new FormData();
  Object.entries(fields).forEach(([k,v]) => form.append(k, v));
  form.append('file', file);
  await fetch(upload_url, { method: 'POST', body: form });

  // 3. Save metadata
  const r3 = await fetch(`/bookings/${bookingId}/images`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      image_key,
      image_order: order,
      content_type: file.type,
      file_size: file.size
    })
  });
  return await r3.json();
}

// Get images
async function getImages(bookingId) {
  const r = await fetch(`/bookings/${bookingId}/images`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { images } = await r.json();
  return images; // Each has temporary 'url' field
}
```
