# Create Job API With Location Coordinates

This document is the frontend contract for creating jobs with optional map coordinates.

## Endpoint

- Method: `POST`
- Path: `/jobs`
- Auth: `Authorization: Bearer <JWT_TOKEN>`

Base URL used elsewhere in frontend docs:

`https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`

Full URL:

`https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/jobs`

## Request Body

Required fields:

- `title`
- `description`
- `location_address`

Optional fields:

- `category`
- `location_city`
- `location_state`
- `location_zip`
- `location_lat`
- `location_lng`
- `preferred_date`
- `preferred_time`
- `budget_min`
- `budget_max`

Example:

```json
{
  "title": "Fix leaking kitchen sink",
  "description": "Sink has been leaking for 2 days, need urgent repair",
  "category": "plumber",
  "location_address": "123 Main St",
  "location_city": "Toronto",
  "location_state": "ON",
  "location_zip": "M5H 1J9",
  "location_lat": 43.6532,
  "location_lng": -79.3832,
  "preferred_date": "2026-03-28",
  "preferred_time": "14:00",
  "budget_min": 100,
  "budget_max": 150
}
```

## Coordinate Fields

- `location_lat`: number, optional
- `location_lng`: number, optional
- Send both together when the user selects a place from autocomplete or a map pin.
- If coordinates are unknown, send `null` or omit both fields.

Frontend recommendation:

- Keep using the formatted address fields for display.
- Use `location_lat` and `location_lng` for map centering, distance calculations, and provider-side location context.

## Success Response

Status: `201 Created`

```json
{
  "message": "Job created successfully",
  "job": {
    "job_id": 123,
    "customer_id": 45,
    "title": "Fix leaking kitchen sink",
    "description": "Sink has been leaking for 2 days, need urgent repair",
    "category": "plumber",
    "location": {
      "address": "123 Main St",
      "city": "Toronto",
      "state": "ON",
      "zip": "M5H 1J9",
      "lat": 43.6532,
      "lng": -79.3832
    },
    "preferred_date": "2026-03-28",
    "preferred_time": "14:00:00",
    "budget": {
      "min": 100.0,
      "max": 150.0
    },
    "status": "open",
    "assigned_provider_id": null,
    "created_at": "2026-03-25T23:04:47",
    "updated_at": "2026-03-25T23:04:47"
  }
}
```

## Error Responses

- `400`: invalid JSON, missing required fields, invalid date/time, or invalid budget range
- `401`: missing or invalid JWT identity
- `404`: customer profile not found
- `500`: internal server error

Example `400`:

```json
{
  "message": "Missing required fields",
  "missing": ["title"]
}
```

## Frontend Fetch Example

```ts
type CreateJobPayload = {
  title: string;
  description: string;
  category?: string | null;
  location_address: string;
  location_city?: string | null;
  location_state?: string | null;
  location_zip?: string | null;
  location_lat?: number | null;
  location_lng?: number | null;
  preferred_date?: string | null;
  preferred_time?: string | null;
  budget_min?: number | null;
  budget_max?: number | null;
};

export async function createJob(token: string, payload: CreateJobPayload) {
  const response = await fetch(
    "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/jobs",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Failed to create job");
  }

  return data.job;
}
```

## Frontend Notes

- The backend returns `location.lat` and `location.lng` as numbers or `null`.
- Keep job cards resilient to missing coordinates.
- Do not derive coordinates from the address on the client after create if the place picker already returned them; send the same values used to render the map.
