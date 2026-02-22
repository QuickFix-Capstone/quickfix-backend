# Customer Public Profile - Frontend Integration Guide

## Overview

This guide covers provider-side frontend integration for:

- `GET /provider/customers/{customer_id}/profile`
- `GET /provider/customers/{customer_id}/reviews`

Base URL:

`https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`

Auth:

- JWT required (`Authorization: Bearer <id_token>`)
- Route is protected with API Gateway JWT authorizer (`z8zn33`)

## Access Model

Customer visibility rules:

1. `public`: any authenticated provider can view
2. `restricted`: provider must have prior interaction with the customer
3. `private`: access denied

Typical frontend behavior:

1. `403` with `"No prior interaction with this customer"`:
- show gated state (not error crash), e.g. “Profile unlocks after first interaction”
2. `403` with `"Profile is private"`:
- show private profile state
3. `404`:
- customer not found

## API 1: Customer Public Profile

Endpoint:

`GET /provider/customers/{customer_id}/profile`

Example:

```http
GET /provider/customers/13/profile
Authorization: Bearer <JWT>
```

Success response (`200`):

```json
{
  "customer": {
    "customer_id": 13,
    "display_name": "Test Y.",
    "avatar_url": null,
    "member_since": "2026-01-25 01:25:55",
    "is_new": true
  },
  "stats": {
    "avg_rating": 3.67,
    "review_count": 2,
    "jobs_posted_6mo": 8,
    "jobs_completed": 3,
    "jobs_cancelled": 1,
    "completion_rate": 37.5,
    "cancellation_rate": 12.5,
    "avg_response_time_minutes": null
  },
  "recent_reviews": [],
  "job_categories": [],
  "badges": []
}
```

Frontend fetch:

```ts
export async function fetchCustomerProfile(customerId: number, token: string) {
  const res = await fetch(
    `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/provider/customers/${customerId}/profile`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  const body = await res.json();
  if (!res.ok) throw { status: res.status, body };
  return body;
}
```

## API 2: Customer Public Reviews

Endpoint:

`GET /provider/customers/{customer_id}/reviews`

Query params:

- `limit` (1-50, default 10)
- `cursor` (review_id based pagination cursor)
- `sort` (`recent` | `highest` | `lowest`)

Example:

```http
GET /provider/customers/13/reviews?limit=10&sort=recent
Authorization: Bearer <JWT>
```

Success response (`200`):

```json
{
  "reviews": [],
  "pagination": {
    "has_more": false,
    "next_cursor": null,
    "limit": 10
  }
}
```

Frontend fetch:

```ts
export async function fetchCustomerReviews(
  customerId: number,
  token: string,
  params: { limit?: number; cursor?: number; sort?: "recent" | "highest" | "lowest" } = {}
) {
  const qp = new URLSearchParams();
  if (params.limit) qp.set("limit", String(params.limit));
  if (params.cursor) qp.set("cursor", String(params.cursor));
  if (params.sort) qp.set("sort", params.sort);

  const url = `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/provider/customers/${customerId}/reviews${qp.toString() ? `?${qp}` : ""}`;
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  const body = await res.json();
  if (!res.ok) throw { status: res.status, body };
  return body;
}
```

## Recommended UI States

1. `loading`
2. `profile loaded`
3. `restricted locked` (`403` no interaction)
4. `private profile` (`403` private)
5. `not found` (`404`)
6. `generic error` (`5xx`/network)

## Testing This Flow

Use script:

`python3 scripts/test_customer_public_profile_endpoints.py --provider-token-file /tmp/jwt_token.txt`

What it verifies:

1. Restricted/no interaction returns `403`
2. Temporary interaction insertion allows `200`
3. Reviews endpoint sort validation returns `400` for invalid sort
4. Cleanup removes temporary interaction row

