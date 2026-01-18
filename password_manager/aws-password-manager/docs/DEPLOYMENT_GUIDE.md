# AWS Secure Password Manager - Deployment Guide

This guide provides comprehensive instructions for deploying a secure, ultra-low-cost password manager on AWS using Cognito, Lambda, API Gateway, DynamoDB, KMS, and S3.

## Architecture Overview

The password manager consists of the following AWS components:

1. **AWS Cognito User Pools**: Handles user authentication with username/password, MFA support, and password policies
2. **AWS Lambda Functions**: Python backend for password CRUD operations and encryption/decryption
3. **Amazon API Gateway**: Exposes Lambda functions through secure HTTPS endpoints
4. **Amazon DynamoDB**: Stores encrypted passwords with per-user isolation
5. **AWS KMS**: Encrypts and decrypts passwords using customer managed keys
6. **Amazon S3**: Hosts the React web application as a static website

## Prerequisites

Before starting, ensure you have:

- An AWS account with appropriate permissions
- AWS CLI installed and configured (`aws configure`)
- Node.js 18+ and npm installed (for React frontend)
- Python 3.9+ installed (for Lambda functions)
- Basic understanding of AWS services

## Cost Estimation

This solution is designed to be ultra-low-cost:
- **Cognito**: First 50,000 MAUs free
- **Lambda**: 1M free requests/month + 400,000 GB-seconds of compute
- **API Gateway**: 1M API calls free for 12 months
- **DynamoDB**: 25GB free storage, 25 read/write capacity units
- **KMS**: $1/month for customer managed key + $0.03 per 10,000 requests
- **S3**: First 5GB free, minimal data transfer for static hosting

**Expected Monthly Cost**: $1-5/month for personal use

---

## Part 1: AWS Cognito User Pool Setup

### Step 1: Create Cognito User Pool

1. Navigate to **AWS Cognito** in the AWS Console
2. Click **Create user pool**

### Step 2: Configure Sign-in Experience

1. **Provider types**: Select `Cognito user pool`
2. **Cognito user pool sign-in options**: Check `Username` and `Email`
3. Click **Next**

### Step 3: Configure Security Requirements

1. **Password policy mode**: Select `Cognito defaults` or customize:
   - Minimum length: 8 characters
   - Require numbers: Yes
   - Require special characters: Yes
   - Require uppercase letters: Yes
   - Require lowercase letters: Yes

2. **Multi-factor authentication (MFA)**: Choose your preference:
   - `No MFA` - For development
   - `Optional MFA` - Recommended for production
   - `Require MFA` - Maximum security

3. **User account recovery**: Select `Email only`

4. Click **Next**

### Step 4: Configure Sign-up Experience

1. **Self-service sign-up**: Enable
2. **Attribute verification and user account confirmation**: 
   - Check `Allow Cognito to automatically send messages to verify and confirm`
   - Select `Send email message, verify email address`
3. **Required attributes**: Select `email`
4. Click **Next**

### Step 5: Configure Message Delivery

1. **Email provider**: Select `Send email with Cognito`
2. **FROM email address**: Use default or configure SES for production
3. Click **Next**

### Step 6: Integrate Your App

1. **User pool name**: Enter `password-manager-user-pool`
2. **Hosted authentication pages**: Uncheck (we use custom UI)
3. **Domain**: Skip (not needed for custom UI)

4. **Initial app client**:
   - **App client name**: `password-manager-web-client`
   - **Client secret**: Select `Don't generate a client secret` (for web apps)
   - **Authentication flows**: Check:
     - `ALLOW_USER_PASSWORD_AUTH`
     - `ALLOW_REFRESH_TOKEN_AUTH`

5. Click **Next**

### Step 7: Review and Create

1. Review all settings
2. Click **Create user pool**
3. **Save the following values** (you'll need them later):
   - User Pool ID (e.g., `us-east-1_aBcDeFgHi`)
   - App Client ID (e.g., `1234567890abcdefghijklmnop`)

---

## Part 2: AWS DynamoDB Table Setup

### Step 1: Create DynamoDB Table

1. Navigate to **DynamoDB** in AWS Console
2. Click **Create table**

### Step 2: Configure Table Settings

1. **Table name**: `PasswordManager`
2. **Partition key**: `user_id` (String)
3. **Sort key**: `password_id` (String)
4. **Table settings**: Select `Customize settings`

### Step 3: Configure Table Class and Capacity

1. **Table class**: `DynamoDB Standard`
2. **Read/write capacity settings**: 
   - Select `On-demand` for variable workloads
   - OR select `Provisioned` with:
     - Read capacity: 5 units
     - Write capacity: 5 units
     - Enable auto scaling: Yes

### Step 4: Configure Encryption

1. **Encryption at rest**: Select `Owned by Amazon DynamoDB` (free)
2. OR select `AWS managed key` for additional security
3. Click **Create table**

### Step 5: Configure Time to Live (Optional)

For automatic cleanup of old deleted items (optional):
1. Select your table
2. Go to **Additional settings** > **Time to Live**
3. Enable TTL with attribute name: `ttl` (requires code modification)

---

## Part 3: AWS KMS Key Setup

### Step 1: Create KMS Key

1. Navigate to **AWS Key Management Service (KMS)**
2. Click **Create key**

### Step 2: Configure Key

1. **Key type**: `Symmetric`
2. **Key usage**: `Encrypt and decrypt`
3. **Advanced options**: Keep defaults
4. Click **Next**

### Step 3: Add Labels

1. **Alias**: `password-manager-encryption-key`
2. **Description**: `KMS key for encrypting password manager passwords`
3. Click **Next**

### Step 4: Define Key Administrative Permissions

1. Select the IAM users/roles that can administer this key
2. Include your user account
3. Click **Next**

### Step 5: Define Key Usage Permissions

1. Select the IAM roles that can use this key (you'll add Lambda role later)
2. Click **Next**

### Step 6: Review and Create

1. Review the key policy
2. Click **Finish**
3. **Save the Key ARN** (e.g., `arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012`)
4. **Save the Key ID** (e.g., `12345678-1234-1234-1234-123456789012`)

---

## Part 4: AWS Lambda Functions Setup

### Step 1: Create IAM Role for Lambda

1. Navigate to **IAM** > **Roles**
2. Click **Create role**
3. **Trusted entity type**: `AWS service`
4. **Use case**: `Lambda`
5. Click **Next**

### Step 2: Attach Permissions Policies

Attach the following policies:
1. `AWSLambdaBasicExecutionRole` (for CloudWatch logs)
2. Create a custom inline policy with the following JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/PasswordManager"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "YOUR_KMS_KEY_ARN"
    }
  ]
}
```

Replace `REGION`, `ACCOUNT_ID`, and `YOUR_KMS_KEY_ARN` with your values.

3. **Role name**: `password-manager-lambda-role`
4. Click **Create role**

### Step 3: Create Password Manager Lambda Function

1. Navigate to **Lambda** in AWS Console
2. Click **Create function**
3. **Function name**: `password-manager-api`
4. **Runtime**: `Python 3.11` or `Python 3.12`
5. **Architecture**: `x86_64`
6. **Permissions**: Select `Use an existing role` and choose `password-manager-lambda-role`
7. Click **Create function**

### Step 4: Configure Lambda Function

1. **Code**: Copy the content from `backend/lambda/password_manager.py`
2. In the Lambda code editor, paste the code
3. Click **Deploy**

### Step 5: Configure Environment Variables

1. Go to **Configuration** > **Environment variables**
2. Click **Edit** > **Add environment variable**
3. Add the following variables:
   - `DYNAMODB_TABLE`: `PasswordManager`
   - `KMS_KEY_ID`: Your KMS Key ID (from Part 3)
4. Click **Save**

### Step 6: Configure Function Settings

1. Go to **Configuration** > **General configuration**
2. Click **Edit**
3. Set:
   - **Memory**: 256 MB
   - **Timeout**: 30 seconds
4. Click **Save**

### Step 7: Create Decrypt Password Lambda Function

1. Repeat steps 2-6 above with:
   - **Function name**: `decrypt-password-api`
   - **Code**: Use content from `backend/lambda/decrypt_password.py`
   - Same environment variables and settings

---

## Part 5: API Gateway Setup

### Step 1: Create REST API

1. Navigate to **API Gateway** in AWS Console
2. Click **Create API**
3. Choose **REST API** (not Private)
4. Click **Build**

### Step 2: Configure API

1. **Choose the protocol**: `REST`
2. **Create new API**: `New API`
3. **API name**: `password-manager-api`
4. **Description**: `API for secure password manager`
5. **Endpoint Type**: `Regional`
6. Click **Create API**

### Step 3: Create Cognito Authorizer

1. In your API, click **Authorizers** in the left menu
2. Click **Create New Authorizer**
3. **Name**: `cognito-authorizer`
4. **Type**: `Cognito`
5. **Cognito User Pool**: Select your user pool
6. **Token Source**: `Authorization`
7. Click **Create**

### Step 4: Create Resources and Methods

#### Create /passwords resource:

1. Click **Actions** > **Create Resource**
2. **Resource Name**: `passwords`
3. **Resource Path**: `passwords`
4. Enable **CORS**
5. Click **Create Resource**

#### Add GET method (List passwords):

1. Select `/passwords` resource
2. Click **Actions** > **Create Method** > Select `GET`
3. **Integration type**: `Lambda Function`
4. **Use Lambda Proxy integration**: Check
5. **Lambda Function**: `password-manager-api`
6. Click **Save** and **OK**

#### Add POST method (Create password):

1. Select `/passwords` resource
2. Click **Actions** > **Create Method** > Select `POST`
3. Configure same as GET method
4. Click **Save**

#### Create /passwords/{id} resource:

1. Select `/passwords` resource
2. Click **Actions** > **Create Resource**
3. **Resource Name**: `password`
4. **Resource Path**: `{id}`
5. Enable **CORS**
6. Click **Create Resource**

#### Add GET, PUT, DELETE methods:

For each method (GET, PUT, DELETE):
1. Select `/passwords/{id}` resource
2. Click **Actions** > **Create Method**
3. Configure Lambda proxy integration with `password-manager-api`

#### Create /decrypt/{id} resource:

1. Click **Actions** > **Create Resource**
2. **Resource Name**: `decrypt`
3. **Resource Path**: `decrypt`
4. Enable **CORS**
5. Click **Create Resource**
6. Create child resource `{id}`
7. Add GET method with `decrypt-password-api` Lambda function

### Step 5: Enable Cognito Authorization

For each method (except OPTIONS):
1. Click on the method
2. Click **Method Request**
3. Click edit pencil on **Authorization**
4. Select `cognito-authorizer`
5. Click the checkmark to save

### Step 6: Enable CORS

For each resource:
1. Select the resource
2. Click **Actions** > **Enable CORS**
3. Keep default settings or customize
4. Click **Enable CORS and replace existing CORS headers**

### Step 7: Deploy API

1. Click **Actions** > **Deploy API**
2. **Deployment stage**: `[New Stage]`
3. **Stage name**: `prod`
4. Click **Deploy**
5. **Save the Invoke URL** (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)

---

## Part 6: React Frontend Deployment

### Step 1: Configure Frontend

1. Navigate to the frontend directory:
   ```bash
   cd password_manager/aws-password-manager/frontend
   ```

2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your AWS values:
   ```
   REACT_APP_AWS_REGION=us-east-1
   REACT_APP_COGNITO_USER_POOL_ID=your-user-pool-id
   REACT_APP_COGNITO_CLIENT_ID=your-client-id
   REACT_APP_API_BASE_URL=https://your-api-gateway-url/prod
   ```

### Step 2: Install Dependencies

```bash
npm install
```

### Step 3: Build the Application

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

### Step 4: Create S3 Bucket for Static Hosting

1. Navigate to **S3** in AWS Console
2. Click **Create bucket**
3. **Bucket name**: `password-manager-web-app-YOUR_UNIQUE_ID` (must be globally unique)
4. **Region**: Same as your other resources
5. **Block Public Access settings**: UNCHECK "Block all public access"
6. Acknowledge the warning
7. Click **Create bucket**

### Step 5: Configure Bucket for Static Website Hosting

1. Select your bucket
2. Go to **Properties** tab
3. Scroll to **Static website hosting**
4. Click **Edit**
5. **Static website hosting**: Enable
6. **Hosting type**: `Host a static website`
7. **Index document**: `index.html`
8. **Error document**: `index.html`
9. Click **Save changes**
10. **Save the bucket website endpoint** URL

### Step 6: Configure Bucket Policy

1. Go to **Permissions** tab
2. Scroll to **Bucket policy**
3. Click **Edit**
4. Paste the following policy (replace `YOUR_BUCKET_NAME`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
    }
  ]
}
```

5. Click **Save changes**

### Step 7: Upload Build Files

Using AWS CLI:
```bash
cd build
aws s3 sync . s3://your-bucket-name/ --acl public-read
```

Or manually:
1. Go to **Objects** tab
2. Click **Upload**
3. Add all files from the `build/` directory
4. Click **Upload**

### Step 8: Configure CORS on API Gateway

Update your API Gateway CORS settings to include your S3 website URL:

1. Go to API Gateway > Your API
2. Select each resource
3. Click **Actions** > **Enable CORS**
4. Set `Access-Control-Allow-Origin` to your S3 website URL or `*` for development
5. Deploy the API again

---

## Part 7: Testing the Application

### Step 1: Access the Application

1. Open your browser
2. Navigate to your S3 website endpoint URL
3. You should see the login page

### Step 2: Register a New User

1. Click **Register**
2. Enter username, email, and password
3. Click **Register**
4. Check your email for verification code
5. Enter the verification code
6. Click **Verify**

### Step 3: Sign In

1. Enter your username and password
2. Click **Sign In**
3. You should be redirected to the dashboard

### Step 4: Test Password Operations

1. Click **Add Password**
2. Fill in the form:
   - Site Name: `Test Site`
   - Username: `testuser`
   - Click **Generate** to create a random password
3. Click **Save**
4. You should see the password card in the dashboard
5. Click **View** to reveal the password
6. Test **Edit** and **Delete** operations

---

## Security Best Practices

### 1. Enable MFA on Cognito

For production, enable MFA in Cognito User Pool settings:
- Go to User Pool > Sign-in experience
- Set MFA to `Optional` or `Required`

### 2. Use CloudFront for S3

Instead of direct S3 hosting, use CloudFront for HTTPS:
1. Create CloudFront distribution
2. Point to S3 bucket
3. Enable HTTPS only
4. Add custom domain with SSL certificate

### 3. Restrict CORS

Update API Gateway CORS to only allow your domain:
- Change `Access-Control-Allow-Origin` from `*` to your domain
- Update Lambda functions' CORS responses

### 4. Enable API Gateway Throttling

1. Go to API Gateway > Usage Plans
2. Create usage plan with throttling limits
3. Attach to your API stage

### 5. Enable CloudWatch Logging

1. Enable CloudWatch logs for Lambda functions
2. Enable API Gateway access logs
3. Set up alarms for errors

### 6. Rotate KMS Keys

1. Enable automatic key rotation in KMS
2. Or manually rotate keys annually

### 7. Regular Backups

1. Enable DynamoDB Point-in-Time Recovery
2. Or set up regular backups to S3

### 8. Monitor Costs

1. Set up AWS Budget alerts
2. Monitor CloudWatch metrics
3. Review AWS Cost Explorer monthly

---

## Troubleshooting

### Issue: Cannot Sign In

**Solutions**:
- Verify Cognito User Pool ID and Client ID are correct in `.env`
- Check if user is confirmed (verify email)
- Check browser console for errors

### Issue: API Calls Fail with 401 Unauthorized

**Solutions**:
- Verify API Gateway authorizer is configured
- Check if Cognito token is being sent
- Verify Lambda function has correct environment variables

### Issue: Cannot Decrypt Passwords

**Solutions**:
- Verify KMS key ID is correct
- Check Lambda IAM role has KMS decrypt permissions
- Verify KMS key policy allows Lambda role

### Issue: CORS Errors

**Solutions**:
- Enable CORS on all API Gateway resources
- Update Lambda CORS headers to match frontend origin
- Clear browser cache

### Issue: S3 Website Not Loading

**Solutions**:
- Verify bucket policy allows public read
- Check static website hosting is enabled
- Verify index.html exists in bucket root

---

## Updating the Application

### Update Frontend

```bash
cd frontend
npm run build
aws s3 sync build/ s3://your-bucket-name/ --delete --acl public-read
```

### Update Lambda Functions

1. Modify the Lambda function code
2. In AWS Console, paste new code
3. Click **Deploy**

Or use AWS CLI:
```bash
zip function.zip lambda_function.py
aws lambda update-function-code --function-name password-manager-api --zip-file fileb://function.zip
```

---

## Cleanup (Deleting Resources)

To avoid charges, delete resources in this order:

1. Empty and delete S3 bucket
2. Delete API Gateway API
3. Delete Lambda functions
4. Delete DynamoDB table
5. Schedule KMS key deletion (7-30 days)
6. Delete Cognito User Pool
7. Delete IAM roles and policies

---

## Cost Optimization Tips

1. Use DynamoDB on-demand pricing for variable workloads
2. Set API Gateway caching if needed
3. Use S3 lifecycle policies to delete old access logs
4. Monitor and set up billing alerts
5. Consider reserved capacity for predictable workloads

---

## Next Steps

1. **Custom Domain**: Set up custom domain with Route 53 and CloudFront
2. **Enhanced Security**: Enable AWS WAF on API Gateway
3. **Monitoring**: Set up comprehensive CloudWatch dashboards
4. **Backup**: Implement automated DynamoDB backups
5. **CI/CD**: Set up automated deployment pipeline
6. **Mobile App**: Create mobile version with React Native
7. **Password Sharing**: Add secure password sharing features
8. **Audit Logs**: Track all password access events

---

## Support and Resources

- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [AWS KMS Documentation](https://docs.aws.amazon.com/kms/)
- [React Documentation](https://react.dev/)

---

## License

This project is provided as-is for educational and personal use.
