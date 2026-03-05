# Payment Quote API Documentation

## Overview

The Payment Quote API calculates the total payment amount for a completed job, including base price, taxes, and application fees. This endpoint should be called before initiating payment to get the exact breakdown of charges.

---

## Endpoint

**POST** `/payment-quote` (or your configured Lambda endpoint)

---

## Authentication

**Required:** Yes

This endpoint requires a valid JWT token in the request headers.

```http
Authorization: Bearer <your-jwt-token>
```

The JWT token must contain a `sub` (subject) claim that identifies the authenticated user.

---

## Request

### Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | Bearer token for authentication |
| `Content-Type` | string | Yes | Must be `application/json` |

### Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | number/string | Yes | The unique identifier of the job to get payment quote for |

### Example Request

```json
{
  "job_id": 12345
}
```

---

## Response

### Success Response (200 OK)

#### New Payment Quote

When the job hasn't been paid yet, the API returns a calculated quote:

```json
{
  "job_id": 12345,
  "location_state": "Ontario",
  "normalized_state": "ON",
  "tax_rate": 0.13,
  "app_fee_rate": 0.07,
  "amounts": {
    "base_amount_cents": 10000,
    "tax_cents": 1300,
    "app_fee_cents": 700,
    "final_amount_cents": 12000,
    "currency": "cad"
  }
}
```

#### Already Paid

If the job has already been paid, the API returns the existing payment information:

```json
{
  "already_paid": true,
  "payment_id": "pay_abc123xyz",
  "amounts": {
    "base_amount_cents": 10000,
    "tax_cents": 1300,
    "app_fee_cents": 700,
    "final_amount_cents": 12000,
    "currency": "cad"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | number | The job identifier (only in new quotes) |
| `location_state` | string | The original state/province name from the job |
| `normalized_state` | string | The standardized state/province code (e.g., "ON", "BC") |
| `tax_rate` | number | The tax rate applied (decimal, e.g., 0.13 = 13%) |
| `app_fee_rate` | number | The application fee rate (decimal, e.g., 0.07 = 7%) |
| `already_paid` | boolean | Indicates if this job has already been paid |
| `payment_id` | string | The existing payment ID (only if already paid) |
| `amounts` | object | Breakdown of all payment amounts |
| `amounts.base_amount_cents` | number | Base job price in cents |
| `amounts.tax_cents` | number | Tax amount in cents |
| `amounts.app_fee_cents` | number | Application fee in cents |
| `amounts.final_amount_cents` | number | Total amount to charge in cents |
| `amounts.currency` | string | Currency code (lowercase, e.g., "cad") |

---

## Error Responses

### 400 Bad Request

Missing required parameter:

```json
{
  "error": "job_id is required"
}
```

### 401 Unauthorized

Invalid or missing authentication token:

```json
{
  "error": "Unauthorized"
}
```

### 403 Forbidden

#### Customer Not Found

```json
{
  "error": "Customer not found for token"
}
```

#### Job Doesn't Belong to Customer

```json
{
  "error": "Forbidden: job does not belong to this customer"
}
```

### 404 Not Found

Job doesn't exist:

```json
{
  "error": "Job not found"
}
```

### 409 Conflict

#### Job Not Completed

```json
{
  "error": "Job must be completed before payment",
  "details": {
    "status": "in_progress"
  }
}
```

#### Missing Final Price

```json
{
  "error": "Job final_price is missing"
}
```

### 500 Internal Server Error

Server-side error:

```json
{
  "error": "Server error",
  "details": "Error message details"
}
```

---

## Business Logic

### Payment Calculation

The final payment amount is calculated as follows:

1. **Base Amount**: Taken from the job's `final_price` field
2. **Tax**: Calculated based on the job's location state/province
3. **Application Fee**: 7% of the base amount (configurable via `APP_FEE_RATE` environment variable)
4. **Final Amount**: Base + Tax + App Fee

**Formula:**
```
base_amount_cents = final_price * 100
tax_cents = base_amount_cents * tax_rate
app_fee_cents = base_amount_cents * app_fee_rate
final_amount_cents = base_amount_cents + tax_cents + app_fee_cents
```

### Prerequisites

Before calling this endpoint, ensure:

1. ✅ The job status is `"completed"`
2. ✅ The job has a `final_price` set
3. ✅ The authenticated user is the customer who owns the job

### Idempotency

- If a job has already been paid (`status: "paid"`), the endpoint returns the existing payment details instead of calculating a new quote
- This prevents duplicate payments and ensures consistency

---

## Frontend Integration Examples

### React/JavaScript Example

```javascript
async function getPaymentQuote(jobId, authToken) {
  try {
    const response = await fetch('https://your-api-gateway-url/payment-quote', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        job_id: jobId
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get payment quote');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching payment quote:', error);
    throw error;
  }
}

// Usage
const quote = await getPaymentQuote(12345, userToken);

if (quote.already_paid) {
  console.log('This job has already been paid');
  console.log('Payment ID:', quote.payment_id);
} else {
  console.log('Total to pay:', quote.amounts.final_amount_cents / 100, quote.amounts.currency.toUpperCase());
}
```

### Displaying Payment Breakdown

```javascript
function PaymentBreakdown({ quote }) {
  const formatCurrency = (cents) => {
    return (cents / 100).toFixed(2);
  };

  if (quote.already_paid) {
    return (
      <div className="alert alert-info">
        This job has already been paid (Payment ID: {quote.payment_id})
      </div>
    );
  }

  return (
    <div className="payment-breakdown">
      <h3>Payment Summary</h3>
      <div className="line-item">
        <span>Base Amount:</span>
        <span>${formatCurrency(quote.amounts.base_amount_cents)}</span>
      </div>
      <div className="line-item">
        <span>Tax ({(quote.tax_rate * 100).toFixed(1)}%):</span>
        <span>${formatCurrency(quote.amounts.tax_cents)}</span>
      </div>
      <div className="line-item">
        <span>Service Fee ({(quote.app_fee_rate * 100).toFixed(1)}%):</span>
        <span>${formatCurrency(quote.amounts.app_fee_cents)}</span>
      </div>
      <div className="line-item total">
        <span><strong>Total:</strong></span>
        <span><strong>${formatCurrency(quote.amounts.final_amount_cents)} {quote.amounts.currency.toUpperCase()}</strong></span>
      </div>
    </div>
  );
}
```

### Error Handling Example

```javascript
async function handlePaymentQuote(jobId, authToken) {
  try {
    const quote = await getPaymentQuote(jobId, authToken);
    return { success: true, data: quote };
  } catch (error) {
    // Handle specific error cases
    if (error.message.includes('Unauthorized')) {
      return { success: false, error: 'Please log in to continue' };
    } else if (error.message.includes('not completed')) {
      return { success: false, error: 'Job must be completed before payment' };
    } else if (error.message.includes('not found')) {
      return { success: false, error: 'Job not found' };
    } else if (error.message.includes('Forbidden')) {
      return { success: false, error: 'You do not have permission to pay for this job' };
    } else {
      return { success: false, error: 'An unexpected error occurred. Please try again.' };
    }
  }
}
```

---

## Testing

### Test Scenarios

1. **Happy Path**: Request quote for a completed job
   - Expected: 200 OK with calculated amounts

2. **Already Paid**: Request quote for a job that's already been paid
   - Expected: 200 OK with `already_paid: true`

3. **Unauthorized**: Request without valid token
   - Expected: 401 Unauthorized

4. **Wrong Customer**: Request quote for another customer's job
   - Expected: 403 Forbidden

5. **Incomplete Job**: Request quote for a job that's not completed
   - Expected: 409 Conflict

6. **Missing Job ID**: Request without `job_id` parameter
   - Expected: 400 Bad Request

### Sample Test Data

```javascript
// Valid request
{
  "job_id": 12345
}

// Expected response (new quote)
{
  "job_id": 12345,
  "location_state": "Ontario",
  "normalized_state": "ON",
  "tax_rate": 0.13,
  "app_fee_rate": 0.07,
  "amounts": {
    "base_amount_cents": 10000,
    "tax_cents": 1300,
    "app_fee_cents": 700,
    "final_amount_cents": 12000,
    "currency": "cad"
  }
}
```

---

## Notes

- All monetary amounts are returned in **cents** to avoid floating-point precision issues
- The currency is always lowercase (e.g., `"cad"`, not `"CAD"`)
- Tax rates are determined by the job's `location_state` field
- The application fee rate defaults to 7% but can be configured server-side
- This endpoint is **read-only** and does not create any payment records (unless the job is already paid)

---

## Support

For questions or issues with this API, please contact the backend team or refer to the main project documentation.
