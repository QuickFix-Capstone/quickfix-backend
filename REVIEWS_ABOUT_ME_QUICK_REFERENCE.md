# Reviews About Me - Quick Reference Card

## 🚀 Quick Deploy

```bash
# 1. Deploy Lambda
./deploy/create_get_customer_reviews_about_me_lambda.sh

# 2. Configure API Gateway (manual step in AWS Console)
# Path: /customer/reviews-about-me
# Method: GET
# Auth: Cognito

# 3. Test
./test_reviews_about_me.sh
```

---

## 📡 Endpoint

```
GET /prod/customer/reviews-about-me
```

**Base URL:** `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com`

---

## 🔑 Authentication

```bash
Authorization: Bearer <JWT_TOKEN>
```

Get token:
```bash
TOKEN=$(./get_customer_token.sh)
```

---

## 📊 Query Parameters

| Param | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `limit` | int | 20 | 1-100 | Results per page |
| `offset` | int | 0 | ≥0 | Pagination offset |
| `sort` | string | "newest" | See below | Sort order |

**Sort options:** `newest`, `oldest`, `highest_rating`, `lowest_rating`

---

## 📝 Example Requests

### Basic Request
```bash
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me' \
  -H "Authorization: Bearer $TOKEN"
```

### With Parameters
```bash
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me?limit=10&sort=highest_rating' \
  -H "Authorization: Bearer $TOKEN"
```

### With Pagination
```bash
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me?limit=5&offset=10' \
  -H "Authorization: Bearer $TOKEN"
```

---

## ✅ Success Response (200)

```json
{
  "reviews": [
    {
      "review_id": 1,
      "job_id": 123,
      "booking_id": null,
      "provider_id": 456,
      "provider_name": "John's Plumbing",
      "provider_rating": 4.8,
      "service_title": "Fix leaking pipe",
      "rating": 5,
      "comment": "Excellent customer!",
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total_count": 1,
    "has_more": false,
    "next_offset": null
  },
  "customer": {
    "customer_id": 1,
    "name": "Jane Doe",
    "total_reviews_received": 1
  }
}
```

---

## ❌ Error Responses

| Code | Message | Cause |
|------|---------|-------|
| 400 | Invalid query parameters | Bad limit/offset/sort |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Customer not found | Email not in database |
| 500 | Internal server error | Database/Lambda error |

---

## 🗄️ Database

**Table:** `provider_customer_reviews`

**Key columns:**
- `customer_id` - Reviewee (me)
- `provider_id` - Reviewer (them)
- `rating` - 1-5 stars
- `comment` - Review text

**Index:** `idx_pc_customer_created (customer_id, created_at DESC)`

---

## 🧪 Testing

### Quick Test
```bash
TOKEN=$(./get_customer_token.sh)
curl -X GET \
  "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me" \
  -H "Authorization: Bearer $TOKEN" | jq '.pagination.total_count'
```

### Full Test Suite
```bash
./test_reviews_about_me.sh
```

### Add Test Data
```bash
mysql -h quickfix-db.c3gy8vvwpwqo.us-east-2.rds.amazonaws.com \
  -u admin -p quickfix < sql/test_data/add_provider_customer_reviews.sql
```

---

## 📱 Frontend Integration

```javascript
const fetchReviewsAboutMe = async (limit = 20, offset = 0, sort = 'newest') => {
  const token = await getAuthToken();
  const url = `${API_BASE}/customer/reviews-about-me?limit=${limit}&offset=${offset}&sort=${sort}`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  return await response.json();
};
```

---

## 🔍 Monitoring

### View Logs
```bash
aws logs tail /aws/lambda/get_customer_reviews_about_me --follow --region us-east-2
```

### Check Function
```bash
aws lambda get-function \
  --function-name get_customer_reviews_about_me \
  --region us-east-2
```

---

## 🆚 vs /customer/reviews

| Feature | `/reviews` | `/reviews-about-me` |
|---------|------------|---------------------|
| **Reviewer** | Customer (me) | Provider |
| **Reviewee** | Provider | Customer (me) |
| **Shows** | Reviews I wrote | Reviews about me |
| **Can edit** | ✅ Yes | ❌ No |

---

## 📚 Documentation

- **Full API Docs:** `docs/API_CUSTOMER_REVIEWS_ABOUT_ME.md`
- **Quick Start:** `docs/REVIEWS_ABOUT_ME_QUICK_START.md`
- **Comparison:** `docs/CUSTOMER_REVIEWS_COMPARISON.md`
- **Checklist:** `REVIEWS_ABOUT_ME_CHECKLIST.md`
- **Summary:** `DEPLOYMENT_SUMMARY_reviews_about_me.md`

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Get fresh token: `./get_customer_token.sh` |
| Empty reviews | Add test data or wait for real reviews |
| 500 Error | Check CloudWatch logs |
| Slow response | Verify database indexes exist |

---

## ✨ Key Features

- ✅ JWT authentication
- ✅ Pagination support
- ✅ Multiple sort options
- ✅ Provider details included
- ✅ Service context shown
- ✅ Optimized queries
- ✅ CORS enabled
- ✅ Error handling

---

## 📞 Quick Commands

```bash
# Deploy
./deploy/create_get_customer_reviews_about_me_lambda.sh

# Test
./test_reviews_about_me.sh

# Get token
TOKEN=$(./get_customer_token.sh)

# Quick test
curl -X GET \
  "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# View logs
aws logs tail /aws/lambda/get_customer_reviews_about_me --follow --region us-east-2

# Check function
aws lambda get-function --function-name get_customer_reviews_about_me --region us-east-2
```

---

## 🎯 Next Steps

1. Deploy Lambda function
2. Configure API Gateway
3. Test endpoint
4. Integrate with frontend
5. Monitor and optimize

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-23
