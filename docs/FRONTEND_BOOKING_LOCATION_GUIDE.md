# Booking Location Guide

This document is the frontend contract for passing booking coordinates from the customer booking flow into the provider-assigned job created after booking acceptance.

## What Changed

When a customer creates a booking, the frontend can now send:

- `service_lat`
- `service_lng`

Those values are stored on the booking. When the provider accepts the booking, the backend copies them into the created job as:

- `location_lat`
- `location_lng`

This gives the booking workflow the same location context as direct job posting.

## Live API Base URL

`https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`

## Customer Create Booking

- Method: `POST`
- Path: `/booking`
- Auth: `Authorization: Bearer <customer JWT>`

Full URL:

`https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/booking`

## Request Body

Required fields:

- `provider_id`
- `service_category`
- `service_description`
- `scheduled_date`
- `scheduled_time`
- `service_address`
- `service_city`
- `service_state`
- `service_postal_code`

Optional fields:

- `service_lat`
- `service_lng`
- `estimated_price`
- `notes`

Example:

```json
{
  "provider_id": "SP-905e16ba-6a34-4423-9b23-e8dd31a4b70d",
  "service_category": "plumber",
  "service_description": "Fix leaking kitchen sink",
  "scheduled_date": "2026-03-28",
  "scheduled_time": "15:00",
  "service_address": "100 King St W",
  "service_city": "Toronto",
  "service_state": "ON",
  "service_postal_code": "M5X 1A9",
  "service_lat": 43.6487,
  "service_lng": -79.3817,
  "estimated_price": 199.99,
  "notes": "Ring the bell on arrival"
}
```

## Coordinate Rules

- Send both `service_lat` and `service_lng` together.
- Use the coordinates returned by your place picker or map interaction.
- If the user typed an address and no coordinates are available, omit both fields or send `null`.
- Do not geocode again after the user already selected a place. Reuse the same coordinates you already have in UI state.

## Success Response

Status: `201 Created`

Example:

```json
{
  "message": "Booking created successfully",
  "booking": {
    "booking_id": 128,
    "customer_id": 13,
    "provider_id": "SP-905e16ba-6a34-4423-9b23-e8dd31a4b70d",
    "provider_name": "KunPeng",
    "service_category": "plumber",
    "service_description": "Fix leaking kitchen sink",
    "scheduled_date": "2026-03-28",
    "scheduled_time": "15:00:00",
    "status": "pending_confirmation",
    "service_address": "100 King St W",
    "service_city": "Toronto",
    "service_state": "ON",
    "service_postal_code": "M5X 1A9",
    "estimated_price": 199.99,
    "final_price": null,
    "notes": "Ring the bell on arrival",
    "created_at": "2026-03-26T00:02:18",
    "updated_at": "2026-03-26T00:02:18"
  }
}
```

Note:

- The create-booking response does not currently echo `service_lat/service_lng`.
- The coordinates are still persisted in the database and used when the provider accepts the booking.

## Provider Accept Booking

- Method: `POST`
- Path: `/bookings/{booking_id}/accept`
- Auth: `Authorization: Bearer <provider JWT>`

Full URL:

`https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/bookings/{booking_id}/accept`

Example success response:

```json
{
  "message": "Booking accepted successfully",
  "booking_id": 128,
  "job_id": 41,
  "status": "confirmed"
}
```

## UI Changes Needed

### Customer Booking Form

Store these values in form state:

- `service_address`
- `service_city`
- `service_state`
- `service_postal_code`
- `service_lat`
- `service_lng`

Recommended source:

- Google Places
- Apple MapKit place selection
- Mapbox geocoder
- Existing address autocomplete already used in the app

### Map Preview

If `service_lat` and `service_lng` exist:

- center the preview map on those coordinates
- place a marker there
- keep the selected formatted address in the text fields

If coordinates do not exist:

- show the address text only
- do not block submission unless your UX requires map accuracy

### Booking Cards / Booking Details

If your booking detail UI already shows address fields, no breaking change is required.

Recommended enhancement:

- when booking data later includes coordinates in a read endpoint, render a static map thumbnail or open-map action
- until then, keep UI resilient and continue displaying the formatted address

### Provider Side

No new request body fields are required for accept.

After acceptance:

- use the returned `job_id` to navigate to the job details page
- job details can use `location_lat/location_lng` for maps, routing, and distance display

## TypeScript Example

```ts
export type CreateBookingPayload = {
  provider_id: string;
  service_category: string;
  service_description: string;
  scheduled_date: string;
  scheduled_time: string;
  service_address: string;
  service_city: string;
  service_state: string;
  service_postal_code: string;
  service_lat?: number | null;
  service_lng?: number | null;
  estimated_price?: number | null;
  notes?: string | null;
};

export async function createBooking(token: string, payload: CreateBookingPayload) {
  const response = await fetch(
    "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/booking",
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
    throw new Error(data.message || "Failed to create booking");
  }

  return data.booking;
}
```

## Example Form Mapping

```ts
const payload = {
  provider_id: selectedProviderId,
  service_category: form.category,
  service_description: form.description,
  scheduled_date: form.date,
  scheduled_time: form.time,
  service_address: place.address,
  service_city: place.city,
  service_state: place.state,
  service_postal_code: place.postalCode,
  service_lat: place.lat ?? null,
  service_lng: place.lng ?? null,
  estimated_price: form.estimatedPrice ?? null,
  notes: form.notes ?? null,
};
```

## Validation Guidance

- `scheduled_date` format: `YYYY-MM-DD`
- `scheduled_time` format: `HH:MM`
- `service_lat` should be a number between `-90` and `90`
- `service_lng` should be a number between `-180` and `180`

Frontend recommendation:

- validate lat/lng only if either field is present
- if one coordinate exists without the other, treat that as invalid client state and either clear both or block submit

## Error Handling

Common create-booking errors:

- `400` missing required fields
- `400` invalid date/time format
- `401` missing or invalid JWT
- `404` provider not found
- `500` server error

Example:

```json
{
  "message": "Missing required fields",
  "missing": ["service_address"]
}
```

## Recommended Frontend Rollout

1. Update the booking form payload type to include `service_lat` and `service_lng`.
2. Wire your address picker to store both formatted address parts and coordinates.
3. Send coordinates only when they are known.
4. Keep existing booking list and booking detail UI unchanged unless you want to add a map preview.
5. Use job location coordinates after provider acceptance for any map-based job screens.

## Verified Live Example

The deployed flow was verified with:

- booking `128`
- created job `41`
- copied values:
  - `service_lat = 43.6487000`
  - `service_lng = -79.3817000`
  - `location_lat = 43.6487000`
  - `location_lng = -79.3817000`
