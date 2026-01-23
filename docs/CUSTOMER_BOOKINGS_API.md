# Customer Bookings API - Frontend Integration Guide

## Overview

This API allows customers to view all their bookings with filtering and pagination support.

**Base URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`

**Authentication**: JWT token required in Authorization header

---

## Endpoint

### Get Customer Bookings

**Method**: `GET`

**URL**: `/customer/bookings`

**Full Endpoint**:
```
GET https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/bookings
```

---

## Authentication

**Required Header**:
```javascript
{
  "Authorization": "Bearer YOUR_JWT_TOKEN"
}
```

**Getting JWT Token** (from your auth context):
```javascript
const token = auth.user?.id_token;
```

---

## Query Parameters

All parameters are optional:

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `status` | string | - | - | Filter by booking status |
| `limit` | number | 20 | 100 | Number of bookings to return |
| `offset` | number | 0 | - | Pagination offset |

### Valid Status Values:
- `pending` - Booking created, awaiting confirmation
- `confirmed` - Provider confirmed the booking
- `in_progress` - Service is being performed
- `completed` - Service completed
- `cancelled` - Booking was cancelled

---

## Request Examples

### Basic Request (Get all bookings)
```javascript
GET /customer/bookings
Authorization: Bearer {token}
```

### Filter by Status
```javascript
GET /customer/bookings?status=pending
Authorization: Bearer {token}
```

### With Pagination
```javascript
GET /customer/bookings?limit=10&offset=0
Authorization: Bearer {token}
```

### Combined Filters
```javascript
GET /customer/bookings?status=completed&limit=20&offset=0
Authorization: Bearer {token}
```

---

## Response Format

### Success Response (200 OK)

```json
{
  "bookings": [
    {
      "booking_id": 6,
      "provider": {
        "provider_id": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
        "name": "walter smith",
        "business_name": "Water Man",
        "rating": 4.5
      },
      "service_category": "MOVING_SERVICES",
      "service_description": "Help with moving furniture",
      "scheduled_date": "2026-01-15",
      "scheduled_time": "12:12:00",
      "status": "pending",
      "location": {
        "address": "4954 Rosebush Rd",
        "city": "Mississauga",
        "state": "ON",
        "postal_code": "L5M 5M8"
      },
      "estimated_price": 150.00,
      "final_price": null,
      "notes": "Please bring moving equipment",
      "created_at": "2026-01-06T03:10:38",
      "updated_at": "2026-01-06T03:10:38",
      "completed_at": null
    }
  ],
  "pagination": {
    "total": 5,
    "limit": 20,
    "offset": 0,
    "has_more": false
  }
}
```

### Response Fields

**Booking Object**:
- `booking_id`: Unique booking identifier
- `provider`: Provider information object
  - `provider_id`: Provider's unique ID
  - `name`: Provider's full name
  - `business_name`: Business name
  - `rating`: Provider rating (0.0 - 5.0)
- `service_category`: Category of service
- `service_description`: Description of the service
- `scheduled_date`: Date of service (YYYY-MM-DD)
- `scheduled_time`: Time of service (HH:MM:SS)
- `status`: Current booking status
- `location`: Service location object
  - `address`: Street address
  - `city`: City name
  - `state`: State/Province
  - `postal_code`: Postal/ZIP code
- `estimated_price`: Estimated cost (nullable)
- `final_price`: Final cost after completion (nullable)
- `notes`: Customer notes
- `created_at`: Booking creation timestamp
- `updated_at`: Last update timestamp
- `completed_at`: Completion timestamp (nullable)

**Pagination Object**:
- `total`: Total number of bookings matching filter
- `limit`: Number of results per page
- `offset`: Current offset
- `has_more`: Boolean indicating if more results exist

---

## Frontend Implementation

### React/JavaScript Example

```javascript
const BASE_URL = 'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod';

async function getCustomerBookings(status = null, limit = 20, offset = 0) {
  // Build query parameters
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());
  
  const url = `${BASE_URL}/customer/bookings?${params.toString()}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${auth.user.id_token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch bookings: ${response.status}`);
  }
  
  return await response.json();
}
```

### Usage Examples

```javascript
// Get all bookings
const allBookings = await getCustomerBookings();

// Get only pending bookings
const pendingBookings = await getCustomerBookings('pending');

// Get completed bookings with pagination
const completedBookings = await getCustomerBookings('completed', 10, 0);

// Load more (next page)
const nextPage = await getCustomerBookings('pending', 10, 10);
```

---

## React Component Example

### Bookings List Component

```jsx
import { useState, useEffect } from 'react';
import { useAuth } from 'react-oidc-context';

function MyBookings() {
  const auth = useAuth();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 20,
    offset: 0,
    has_more: false
  });

  useEffect(() => {
    loadBookings();
  }, [filter]);

  const loadBookings = async (offset = 0) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (filter !== 'all') params.append('status', filter);
      params.append('limit', '20');
      params.append('offset', offset.toString());
      
      const response = await fetch(
        `${BASE_URL}/customer/bookings?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${auth.user.id_token}`
          }
        }
      );
      
      if (!response.ok) throw new Error('Failed to load bookings');
      
      const data = await response.json();
      setBookings(data.bookings);
      setPagination(data.pagination);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    loadBookings(pagination.offset + pagination.limit);
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="my-bookings">
      <h1>My Bookings</h1>
      
      {/* Filter Tabs */}
      <div className="filters">
        <button onClick={() => setFilter('all')}>All</button>
        <button onClick={() => setFilter('pending')}>Pending</button>
        <button onClick={() => setFilter('confirmed')}>Confirmed</button>
        <button onClick={() => setFilter('in_progress')}>In Progress</button>
        <button onClick={() => setFilter('completed')}>Completed</button>
      </div>

      {/* Bookings List */}
      <div className="bookings-list">
        {bookings.length === 0 ? (
          <p>No bookings found</p>
        ) : (
          bookings.map(booking => (
            <BookingCard key={booking.booking_id} booking={booking} />
          ))
        )}
      </div>

      {/* Load More */}
      {pagination.has_more && (
        <button onClick={loadMore}>Load More</button>
      )}
      
      <p>Showing {bookings.length} of {pagination.total} bookings</p>
    </div>
  );
}
```

### Booking Card Component

```jsx
function BookingCard({ booking }) {
  const statusColors = {
    pending: 'orange',
    confirmed: 'blue',
    in_progress: 'purple',
    completed: 'green',
    cancelled: 'red'
  };

  return (
    <div className="booking-card">
      <div className="booking-header">
        <h3>{booking.service_category.replace('_', ' ')}</h3>
        <span 
          className="status-badge" 
          style={{ backgroundColor: statusColors[booking.status] }}
        >
          {booking.status}
        </span>
      </div>

      <div className="booking-details">
        <p><strong>Provider:</strong> {booking.provider.business_name}</p>
        <p><strong>Date:</strong> {formatDate(booking.scheduled_date)}</p>
        <p><strong>Time:</strong> {formatTime(booking.scheduled_time)}</p>
        <p><strong>Location:</strong> {booking.location.address}, {booking.location.city}</p>
        
        {booking.estimated_price && (
          <p><strong>Estimated Price:</strong> ${booking.estimated_price.toFixed(2)}</p>
        )}
        
        {booking.final_price && (
          <p><strong>Final Price:</strong> ${booking.final_price.toFixed(2)}</p>
        )}
      </div>

      <div className="booking-actions">
        <button onClick={() => viewDetails(booking.booking_id)}>
          View Details
        </button>
        {booking.status === 'pending' && (
          <button onClick={() => cancelBooking(booking.booking_id)}>
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}

// Helper functions
function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

function formatTime(timeString) {
  const [hours, minutes] = timeString.split(':');
  const hour = parseInt(hours);
  const ampm = hour >= 12 ? 'PM' : 'AM';
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${minutes} ${ampm}`;
}
```

---

## Error Handling

### Error Responses

**401 Unauthorized**:
```json
{
  "message": "Unauthorized: Missing identity"
}
```
→ JWT token is missing or invalid. Redirect to login.

**404 Not Found**:
```json
{
  "message": "Customer profile not found"
}
```
→ Customer doesn't exist in database.

**400 Bad Request**:
```json
{
  "message": "Invalid status. Must be one of: pending, confirmed, in_progress, completed, cancelled"
}
```
→ Invalid status filter provided.

**500 Internal Server Error**:
```json
{
  "message": "Internal server error"
}
```
→ Server error. Retry or contact support.

### Error Handling Pattern

```javascript
async function getBookingsWithErrorHandling() {
  try {
    const response = await fetch(url, options);
    
    if (response.status === 401) {
      // Token expired - redirect to login
      auth.signoutRedirect();
      return;
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to load bookings');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error loading bookings:', error);
    toast.error(error.message);
    throw error;
  }
}
```

---

## Pagination Implementation

### Infinite Scroll Pattern

```jsx
function InfiniteBookingsList() {
  const [bookings, setBookings] = useState([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const loadMore = async () => {
    if (loading || !hasMore) return;
    
    setLoading(true);
    const data = await getCustomerBookings(null, 20, offset);
    
    setBookings([...bookings, ...data.bookings]);
    setOffset(offset + 20);
    setHasMore(data.pagination.has_more);
    setLoading(false);
  };

  useEffect(() => {
    loadMore();
  }, []);

  return (
    <div>
      {bookings.map(booking => (
        <BookingCard key={booking.booking_id} booking={booking} />
      ))}
      {hasMore && (
        <button onClick={loadMore} disabled={loading}>
          {loading ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

---

## CORS Headers

The API includes the following CORS headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type,Authorization
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
```

**No CORS configuration needed on the frontend!** ✅

---

## Testing

### Test with cURL

```bash
curl -X GET \
  "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/bookings?status=pending&limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Test with Postman

1. **Method**: GET
2. **URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/bookings`
3. **Headers**:
   - `Authorization`: `Bearer YOUR_JWT_TOKEN`
4. **Query Params** (optional):
   - `status`: `pending`
   - `limit`: `10`
   - `offset`: `0`

---

## Performance Tips

1. **Use appropriate limit**: Don't fetch more than needed
   ```javascript
   // Good: Only fetch what you need
   const bookings = await getCustomerBookings(null, 10);
   
   // Bad: Fetching too many at once
   const bookings = await getCustomerBookings(null, 100);
   ```

2. **Cache results**: Store bookings in state/context to avoid refetching
   ```javascript
   const [cachedBookings, setCachedBookings] = useState({});
   ```

3. **Debounce filter changes**: Wait for user to finish selecting filters
   ```javascript
   const debouncedFilter = useDebounce(filter, 300);
   ```

4. **Show loading states**: Improve UX with loading indicators
   ```jsx
   {loading && <Spinner />}
   ```

---

## Summary

**Endpoint**: `GET /customer/bookings`

**Features**:
- ✅ JWT authentication
- ✅ Status filtering
- ✅ Pagination support
- ✅ CORS enabled
- ✅ Provider information included
- ✅ Returns only customer's own bookings

**Ready to use!** 🚀
