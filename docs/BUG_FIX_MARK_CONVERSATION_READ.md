# Bug Fix: `PUT /messages/conversations/{conversationId}/read` — 500 Internal Server Error

**Date:** 2026-03-19  
**Severity:** High  
**Affected Lambda:** `mark_conversation_read`  
**File:** `lambda/messages/mark_conversation_read/handler.py`

---

## Symptom

The frontend call to mark a conversation as read returns a **500 Internal Server Error**:

```
PUT https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/messages/conversations/{conversationId}/read → 500
```

---

## Root Cause

### Bug 1 — Provider `user_id` not converted to string (line 106)

The customer path correctly converts the ID to a string, but the provider path does not:

```diff
 # Customer (line 94) — correct
 user_id = str(user_row["customer_id"])

 # Provider (line 106) — BUG: raw integer
-user_id = user_row["provider_id"]
+user_id = str(user_row["provider_id"])
```

DynamoDB stores `userId` as a **string**. Passing a raw integer causes the `update_item` call to fail with a `ConditionalCheckFailedException` or a type mismatch, which is caught by the generic `except` on line 134 and returned as a 500.

### Bug 2 — Same pattern in `websocket_context.py` (line 106)

`get_user_identity()` also returns the provider's `app_user_id` without `str()`:

```diff
 # File: src/utils/websocket_context.py, line 106
-"app_user_id": provider["provider_id"],
+"app_user_id": str(provider["provider_id"]),
```

This can cause downstream mismatches whenever provider identity is used for DynamoDB lookups or message ownership checks.

---

## Fix Instructions

### Step 1 — Fix `handler.py`

**File:** `lambda/messages/mark_conversation_read/handler.py`

Change **line 106** from:

```python
user_id = user_row["provider_id"]
```

to:

```python
user_id = str(user_row["provider_id"])
```

### Step 2 — Fix `websocket_context.py`

**File:** `src/utils/websocket_context.py`

Change **line 106** from:

```python
"app_user_id": provider["provider_id"],
```

to:

```python
"app_user_id": str(provider["provider_id"]),
```

### Step 3 — Redeploy the Lambda

```bash
# From the project root, run the deploy script:
bash deploy/deploy_mark_conversation_read.sh
```

---

## Verification

After deploying, confirm the fix:

1. **Test via frontend:** Open a conversation as a provider and verify no 500 error in the browser console.
2. **Test via curl / Postman** (see `docs/POSTMAN_MARK_READ.md`):
   ```bash
   curl -X PUT \
     "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/messages/conversations/{conversationId}/read" \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json"
   ```
   Expected: `200` with `{"conversationId": "...", "unreadCount": 0, ...}`
3. **Check CloudWatch Logs:** Confirm no `DynamoDB error` entries for this Lambda.

---

## Additional Recommendation

> [!TIP]
> Search the entire backend for other places where `provider_id` or `customer_id` is used with DynamoDB without `str()` conversion. A quick grep can surface similar bugs:
> ```bash
> grep -rn 'provider_id\|customer_id' lambda/ src/ | grep -v str | grep -v __pycache__
> ```
