# Customer API

This document defines the Customer API for the QuickFix backend.

The API is implemented as an AWS Lambda function:

- Lambda folder: `lambda/customers/create_customer/handler.py`
- Handler function: `handler(event, context)`
- DB: MySQL on AWS RDS (`quickfix` database, `customers` table)

Later, authentication will be handled by AWS Cognito. For now, this API assumes the caller is allowed to register a customer.

---

## 1. Data Model – `customers` Table

**Table name:** `customers`

| Column         | Type           | Notes                                             |
|----------------|----------------|---------------------------------------------------|
| `customer_id`  | BIGINT         | PK, AUTO_INCREMENT                                |
| `first_name`   | VARCHAR(100)   | NOT NULL                                          |
| `last_name`    | VARCHAR(100)   | NOT NULL                                          |
| `email`        | VARCHAR(255)   | NOT NULL, UNIQUE                                  |
| `phone`        | VARCHAR(20)    | NULL                                              |
| `address`      | VARCHAR(255)   | NULL                                              |
| `city`         | VARCHAR(100)   | NULL                                              |
| `state`        | VARCHAR(100)   | NULL                                              |
| `postal_code`  | VARCHAR(20)    | NULL                                              |
| `cognito_sub`  | VARCHAR(255)   | NULL, UNIQUE when present (maps to Cognito user)  |
| `created_at`   | TIMESTAMP      | DEFAULT CURRENT_TIMESTAMP                         |

Notes:

- **Email is unique** → one email = one customer.
- `cognito_sub` is optional now, but used to link a customer to a Cognito user in the future.
- This API only **creates** a customer; other operations (get/update) will be added later.

---

## 2. Endpoint – Create (Register) Customer

### 2.1 Overview

- **Method:** `POST`
- **Path (proposed):** `/customers`
- **Lambda:** `lambda/customers/create_customer/handler.py`
- **Purpose:** Register a new customer in the `customers` table.

Later, this endpoint will usually be called:

- right after a Cognito signup / social login, or  
- during a “complete your profile” flow.

---

### 2.2 Request Format

**Content-Type:** `application/json`

**Body:**

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