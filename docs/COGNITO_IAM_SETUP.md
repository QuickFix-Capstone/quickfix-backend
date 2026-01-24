# IAM Policy Setup for Cognito Group Assignment

## Overview
The `create_customer` Lambda function needs permission to add users to Cognito groups. This must be configured manually in the AWS Console.

## Required IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:AdminAddUserToGroup"
      ],
      "Resource": "arn:aws:cognito-idp:us-east-2:*:userpool/us-east-2_45z5OMePi"
    }
  ]
}
```

## Setup Instructions

### Step 1: Navigate to Lambda IAM Role
1. Go to [AWS Lambda Console](https://us-east-2.console.aws.amazon.com/lambda/home?region=us-east-2#/functions)
2. Click on the `create_customer` function
3. Go to the **Configuration** tab
4. Click **Permissions** in the left sidebar
5. Under "Execution role", click the role name (e.g., `create_customer-role-xxxxx`)
   - This will open the IAM console in a new tab

### Step 2: Add Inline Policy
1. In the IAM Role page, click **Add permissions** → **Create inline policy**
2. Click the **JSON** tab
3. Paste the IAM policy JSON from above
4. Click **Review policy**
5. Name the policy: `CognitoCustomerGroupAccess`
6. Click **Create policy**

### Step 3: Verify Policy
1. Go back to the IAM role page
2. Under "Permissions policies", you should see:
   - The original Lambda execution policy (e.g., `AWSLambdaBasicExecutionRole`)
   - Your new policy: `CognitoCustomerGroupAccess`

## Verification

After adding the policy, test by:

1. Deploy the Lambda function:
   ```bash
   cd /Users/ykpfly/Desktop/capstone/quickfix_backend/deploy
   ./deploy_create_customer.sh
   ```

2. Create a test customer and check CloudWatch logs:
   ```bash
   aws logs tail /aws/lambda/create_customer --follow --region us-east-2
   ```

3. Look for:
   - ✅ `Successfully added [email] to customer group`
   - ❌ If you see permission errors, double-check the IAM policy

## Troubleshooting

**Error: "User: arn:aws:sts::xxx:assumed-role/create_customer-role/create_customer is not authorized to perform: cognito-idp:AdminAddUserToGroup"**

**Solution:** The IAM policy was not added correctly. Verify:
- Policy is attached to the correct role
- Resource ARN matches your User Pool ID
- Action is `cognito-idp:AdminAddUserToGroup`

**Error: "ResourceNotFoundException: Group customer not found"**

**Solution:** The `customer` group doesn't exist in Cognito. Create it:
1. Go to Cognito User Pools → `us-east-2_45z5OMePi`
2. Groups tab → Create group
3. Group name: `customer`
4. Description: "Customer users"
5. Create group

## Security Notes

- This policy only allows adding users to groups, not creating/deleting groups
- The policy is scoped to a specific User Pool (us-east-2_45z5OMePi)
- The Lambda cannot modify other Cognito resources
