# Customer Booking System - Quick Start Guide

## What's Been Created

✅ **Database**: `bookings` table with foreign keys to customers and service_providers  
✅ **Lambda Functions**: 4 functions for complete booking management  
✅ **Deployment Scripts**: Ready-to-use deployment automation  

## Next Steps

### 1. Run Database Migration

Execute the SQL in your session file or run:
```bash
mysql -h <host> -u <user> -p quickfix < sql/migrations/create_bookings_table.sql
```

### 2. Create Lambda Functions in AWS

You need to create 4 Lambda functions first (they don't exist yet):

```bash
# Create create_booking
aws lambda create-function \
  --function-name create_booking \
  --runtime python3.9 \
  --role arn:aws:iam::008971679867:role/service-role/create_customer-role-qch33m23 \
  --handler handler.handler \
  --zip-file fileb://placeholder.zip \
  --region us-east-2 \
  --timeout 30

# Create get_customer_bookings  
aws lambda create-function \
  --function-name get_customer_bookings \
  --runtime python3.9 \
  --role arn:aws:iam::008971679867:role/service-role/create_customer-role-qch33m23 \
  --handler handler.handler \
  --zip-file fileb://placeholder.zip \
  --region us-east-2 \
  --timeout 30

# Create get_booking_details
aws lambda create-function \
  --function-name get_booking_details \
  --runtime python3.9 \
  --role arn:aws:iam::008971679867:role/service-role/create_customer-role-qch33m23 \
  --handler handler.handler \
  --zip-file fileb://placeholder.zip \
  --region us-east-2 \
  --timeout 30

# Create update_booking
aws lambda create-function \
  --function-name update_booking \
  --runtime python3.9 \
  --role arn:aws:iam::008971679867:role/service-role/create_customer-role-qch33m23 \
  --handler handler.handler \
  --zip-file fileb://placeholder.zip \
  --region us-east-2 \
  --timeout 30
```

### 3. Deploy Lambda Code

```bash
cd deploy
./deploy_create_booking.sh
./deploy_get_customer_bookings.sh
./deploy_get_booking_details.sh
./deploy_update_booking.sh
```

### 4. Configure API Gateway Routes

Add these routes to your API Gateway:

| Method | Path | Lambda Function | Auth |
|--------|------|-----------------|------|
| POST | `/bookings` | create_booking | JWT |
| GET | `/bookings` | get_customer_bookings | JWT |
| GET | `/bookings/{booking_id}` | get_booking_details | JWT |
| PUT | `/bookings/{booking_id}` | update_booking | JWT |

### 5. Deploy API Gateway

Deploy your API to make the routes live.

## API Usage Examples

### Create Booking
```bash
POST /bookings
Authorization: Bearer <jwt-token>

{
  "provider_id": 1,
  "service_category": "plumber",
  "service_description": "Fix leaking kitchen sink",
  "scheduled_date": "2026-01-15",
  "scheduled_time": "14:00",
  "customer_address": "123 Main St",
  "customer_city": "Toronto",
  "customer_state": "ON",
  "customer_postal_code": "M5H 1J9",
  "estimated_price": 150.00,
  "notes": "Please call before arriving"
}
```

### Get Customer's Bookings
```bash
GET /bookings?status=pending&limit=20
Authorization: Bearer <jwt-token>
```

### Get Booking Details
```bash
GET /bookings/1
Authorization: Bearer <jwt-token>
```

### Update Booking
```bash
PUT /bookings/1
Authorization: Bearer <jwt-token>

{
  "status": "cancelled",
  "notes": "No longer needed"
}
```

## Files Created

### Database
- `sql/migrations/create_bookings_table.sql` - Migration script
- `sql/quickfix-mysql.sql` - Updated with bookings table
- `quickfix-mySql.session.sql` - Added migration SQL

### Lambda Functions
- `lambda/bookings/create_booking/handler.py`
- `lambda/bookings/get_customer_bookings/handler.py`
- `lambda/bookings/get_booking_details/handler.py`
- `lambda/bookings/update_booking/handler.py`

### Deployment Scripts
- `deploy/deploy_create_booking.sh`
- `deploy/deploy_get_customer_bookings.sh`
- `deploy/deploy_get_booking_details.sh`
- `deploy/deploy_update_booking.sh`

## Testing

Test locally before deploying:
```bash
python lambda/bookings/create_booking/handler.py
python lambda/bookings/get_customer_bookings/handler.py
python lambda/bookings/get_booking_details/handler.py
python lambda/bookings/update_booking/handler.py
```

## Status Workflow

```
pending → confirmed → in_progress → completed
   ↓
cancelled
```

**Customer can:**
- Cancel pending bookings
- Cancel confirmed bookings
- Update notes

**Customer cannot:**
- Cancel in_progress or completed bookings
- Change to confirmed or in_progress (provider only)
