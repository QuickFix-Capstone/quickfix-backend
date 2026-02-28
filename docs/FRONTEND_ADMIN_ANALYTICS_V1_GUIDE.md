# Admin Analytics V1 - Frontend Integration Guide

## Overview

Use this endpoint to load platform-level admin analytics metrics.

- **API**: `GET /admin/analytics/v1`
- **Base URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`
- **Full URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/admin/analytics/v1`
- **Auth**: JWT required, admin group only (`Administrator`)

---

## Authentication

Send JWT in header:

```http
Authorization: Bearer <JWT_TOKEN>
```

Expected behavior:
- `200` for admin users
- `403` for authenticated non-admin users
- `401` for missing/invalid identity

---

## API Contract

### Request

```http
GET /admin/analytics/v1
```

No query params and no body.

### Success Response (200)

```json
{
  "message": "Admin analytics retrieved successfully",
  "generated_at": "2026-02-28T17:52:34.465117+00:00",
  "admin_sub": "b12ba550-c081-70c0-9852-303bd8a7b85a",
  "metrics": {
    "customers_total": 6,
    "providers_total": 26,
    "jobs_total": 10,
    "bookings_total": 7,
    "reviews_total": 3,
    "commitment": {
      "committed_jobs": 10,
      "avg_minutes_to_commitment": 21.8,
      "direct_jobs_committed": 5,
      "avg_minutes_direct": 0,
      "booking_jobs_committed": 5,
      "avg_minutes_booking": 43.6
    }
  }
}
```

### Error Responses

```json
{ "message": "Unauthorized: Missing identity" }
```

```json
{ "message": "Forbidden: Admin access required" }
```

```json
{ "message": "Database connection failed" }
```

---

## Frontend Example (Fetch)

```javascript
const BASE_URL = "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod";

export async function getAdminAnalyticsV1(token) {
  const response = await fetch(`${BASE_URL}/admin/analytics/v1`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    }
  });

  const data = await response.json();

  if (!response.ok) {
    const message = data?.message || "Failed to fetch admin analytics";
    const error = new Error(message);
    error.status = response.status;
    error.payload = data;
    throw error;
  }

  return data;
}
```

---

## TypeScript Types

```ts
export interface AdminAnalyticsV1Response {
  message: string;
  generated_at: string;
  admin_sub: string;
  metrics: {
    customers_total: number;
    providers_total: number;
    jobs_total: number;
    bookings_total: number;
    reviews_total: number;
    commitment: {
      committed_jobs: number;
      avg_minutes_to_commitment: number | null;
      direct_jobs_committed: number;
      avg_minutes_direct: number | null;
      booking_jobs_committed: number;
      avg_minutes_booking: number | null;
    };
  };
}
```

---

## React Usage Example

```jsx
import { useEffect, useState } from "react";
import { getAdminAnalyticsV1 } from "./api/adminAnalytics";

export function AdminDashboard({ token }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        const result = await getAdminAnalyticsV1(token);
        if (mounted) setData(result);
      } catch (err) {
        if (mounted) setError(err.message || "Failed to load analytics");
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [token]);

  if (loading) return <div>Loading analytics...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div>
      <h2>Admin Analytics</h2>
      <p>Customers: {data.metrics.customers_total}</p>
      <p>Providers: {data.metrics.providers_total}</p>
      <p>Jobs: {data.metrics.jobs_total}</p>
      <p>Bookings: {data.metrics.bookings_total}</p>
      <p>Reviews: {data.metrics.reviews_total}</p>
      <p>
        Avg Time to Commitment (min):{" "}
        {data.metrics.commitment.avg_minutes_to_commitment ?? "N/A"}
      </p>
    </div>
  );
}
```

---

## Frontend Handling Rules

1. If `401`: redirect to login.
2. If `403`: show "Admin access required" page.
3. If `500`: show retry UI and keep last known dashboard state.

---

## Quick Manual Test

```bash
./scripts/get_admin_idtoken.sh
curl -H "Authorization: Bearer $(cat /tmp/admin_id_token.txt)" \
  "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/admin/analytics/v1"
```
