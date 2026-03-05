# Customer API (Frontend)

This document is the frontend contract for customer profile endpoints.

## Base URL
`https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`

## Authentication
Send JWT in all requests:

`Authorization: Bearer <JWT_TOKEN>`

## Customer Object

```json
{
  "customer_id": 123,
  "first_name": "Alice",
  "last_name": "Wong",
  "email": "alice@example.com",
  "phone": "416-555-1234",
  "address": "123 King St",
  "city": "Toronto",
  "state": "ON",
  "postal_code": "M5H 1J9",
  "cognito_sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "avatar_url": "https://...",
  "created_at": "2026-03-04T21:17:58"
}
```

`created_at` is the field frontend should use for "Member since".

## 1) Create Customer

- Method: `POST`
- Path: `/customer`

### Request Body

```json
{
  "first_name": "Alice",
  "last_name": "Wong",
  "email": "alice@example.com",
  "phone": "416-555-1234",
  "address": "123 King St",
  "city": "Toronto",
  "state": "ON",
  "postal_code": "M5H 1J9",
  "cognito_sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
}
```

Required fields: `first_name`, `last_name`, `email`

### Success Response (201)

```json
{
  "message": "Customer created successfully",
  "customer": {
    "customer_id": 123,
    "first_name": "Alice",
    "last_name": "Wong",
    "email": "alice@example.com",
    "created_at": "2026-03-04T21:17:58"
  }
}
```

### Common Errors

- `400`: Missing required fields / invalid JSON
- `409`: Email already exists
- `500`: Server error

## 2) Get Current Customer Profile

- Method: `GET`
- Path: `/customer`

Returns the profile for the authenticated customer.

### Success Response (200)

```json
{
  "customer": {
    "customer_id": 123,
    "first_name": "Alice",
    "last_name": "Wong",
    "email": "alice@example.com",
    "phone": "416-555-1234",
    "address": "123 King St",
    "city": "Toronto",
    "state": "ON",
    "postal_code": "M5H 1J9",
    "cognito_sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "avatar_url": "https://...",
    "created_at": "2026-03-04T21:17:58"
  }
}
```

### Common Errors

- `401`: Missing/invalid identity
- `404`: Customer profile not found
- `500`: Server error

## 3) Update Current Customer Profile

- Method: `PUT`
- Path: `/customer`

### Request Body

Send any subset of:

`first_name`, `last_name`, `email`, `phone`, `address`, `city`, `state`, `postal_code`, `avatar_url`

Example:

```json
{
  "phone": "647-555-9988",
  "city": "Mississauga",
  "avatar_url": "https://..."
}
```

### Success Response (200)

```json
{
  "message": "Customer updated successfully",
  "customer": {
    "customer_id": 123,
    "first_name": "Alice",
    "last_name": "Wong",
    "email": "alice@example.com",
    "phone": "647-555-9988",
    "address": "123 King St",
    "city": "Mississauga",
    "state": "ON",
    "postal_code": "M5H 1J9",
    "cognito_sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "avatar_url": "https://...",
    "created_at": "2026-03-04T21:17:58"
  }
}
```

### Common Errors

- `400`: No fields to update / invalid JSON
- `401`: Missing/invalid identity
- `404`: Customer not found
- `409`: Email already exists
- `500`: Server error

## Frontend "Member Since" Usage

Example:

```ts
const memberSince = new Date(customer.created_at).toLocaleDateString(undefined, {
  year: "numeric",
  month: "long"
});
// e.g. "March 2026"
```

Display:

`Member since {memberSince}`
