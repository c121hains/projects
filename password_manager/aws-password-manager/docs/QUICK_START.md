# Quick Start Guide

This guide will help you get your AWS Secure Password Manager up and running quickly.

## Prerequisites

- AWS Account with admin access
- AWS CLI configured (`aws configure`)
- Node.js 18+ and npm installed
- Python 3.9+ installed

## Option 1: Manual Deployment (Recommended for Learning)

Follow the comprehensive [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions.

**Estimated time**: 45-60 minutes

## Option 2: CloudFormation Deployment (Faster)

### Step 1: Deploy Infrastructure

```bash
cd infrastructure

aws cloudformation create-stack \
  --stack-name password-manager-prod \
  --template-body file://cloudformation-template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for stack creation
aws cloudformation wait stack-create-complete \
  --stack-name password-manager-prod
```

### Step 2: Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name password-manager-prod \
  --query 'Stacks[0].Outputs' \
  --output table
```

Save these values:
- `UserPoolId`
- `UserPoolClientId`
- `ApiUrl`
- `KMSKeyId`
- `FrontendBucketName`

### Step 3: Deploy Lambda Functions

The CloudFormation template creates the Lambda functions, but you need to upload the actual code:

```bash
cd ../backend/lambda

# Package and deploy Password Manager function
zip -r function.zip password_manager.py
aws lambda update-function-code \
  --function-name password-manager-prod-api \
  --zip-file fileb://function.zip

# Package and deploy Decrypt function
zip -r function.zip decrypt_password.py
aws lambda update-function-code \
  --function-name password-manager-prod-decrypt \
  --zip-file fileb://function.zip

rm function.zip
```

### Step 4: Configure and Deploy Frontend

```bash
cd ../../frontend

# Create .env file
cat > .env << EOF
REACT_APP_AWS_REGION=us-east-1
REACT_APP_COGNITO_USER_POOL_ID=<your-user-pool-id>
REACT_APP_COGNITO_CLIENT_ID=<your-client-id>
REACT_APP_API_BASE_URL=<your-api-url>
EOF

# Install and build
npm install
npm run build

# Deploy to S3
aws s3 sync build/ s3://<frontend-bucket-name>/ --acl public-read
```

### Step 5: Configure API Gateway (Manual Steps Required)

The CloudFormation template creates basic API Gateway structure, but you need to:

1. Go to API Gateway Console
2. Select your API
3. For each resource and method:
   - Add Cognito Authorizer
   - Enable CORS
4. Deploy API to `prod` stage

### Step 6: Access Your App

Get the frontend URL:
```bash
aws cloudformation describe-stacks \
  --stack-name password-manager-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendURL`].OutputValue' \
  --output text
```

Open the URL in your browser!

## Option 3: Using the Deployment Script

We've provided a helper script for easy deployment:

### Step 1: Complete Initial Setup

First, manually create the AWS resources (Cognito, DynamoDB, KMS, API Gateway) following the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

### Step 2: Configure Frontend

```bash
cd frontend
cp .env.example .env
# Edit .env with your AWS resource IDs
```

### Step 3: Run Deployment Script

```bash
cd ..
./deploy.sh
```

Select option 3 to deploy both Lambda functions and frontend.

## Post-Deployment Steps

### 1. Test the Application

1. Open your frontend URL
2. Click "Register"
3. Create an account with email
4. Check email for verification code
5. Verify and sign in
6. Test creating, viewing, editing, and deleting passwords

### 2. Enable MFA (Recommended)

1. Go to Cognito User Pool
2. Sign-in experience > Multi-factor authentication
3. Set to "Optional" or "Required"

### 3. Secure CORS

Update Lambda functions to restrict CORS:

```python
# In password_manager.py and decrypt_password.py
headers = {
    'Access-Control-Allow-Origin': 'https://your-actual-domain.com',  # Change this!
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}
```

Redeploy Lambda functions after changes.

### 4. Set Up CloudWatch Alarms

Create alarms for:
- Lambda errors
- API Gateway 5xx errors
- DynamoDB throttles

### 5. Enable CloudTrail

For audit logging:
```bash
aws cloudtrail create-trail \
  --name password-manager-audit \
  --s3-bucket-name my-cloudtrail-bucket
  
aws cloudtrail start-logging \
  --name password-manager-audit
```

## Troubleshooting

### Can't Sign In
- Verify email is confirmed in Cognito console
- Check browser console for errors
- Verify User Pool ID and Client ID in .env

### API Calls Fail
- Check API Gateway URL is correct
- Verify Cognito authorizer is enabled on all endpoints
- Check Lambda CloudWatch logs for errors

### CORS Errors
- Enable CORS on all API Gateway resources
- Update Lambda function CORS headers
- Clear browser cache

### Can't Decrypt Passwords
- Verify KMS Key ID is correct in Lambda environment variables
- Check Lambda IAM role has KMS decrypt permissions

## Cost Monitoring

Set up a budget alert:

```bash
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget.json

# Create budget.json with your desired threshold
```

## Cleanup

To delete all resources and avoid charges:

```bash
# If using CloudFormation:
aws cloudformation delete-stack --stack-name password-manager-prod

# If manual deployment:
# 1. Empty and delete S3 bucket
# 2. Delete API Gateway
# 3. Delete Lambda functions
# 4. Delete DynamoDB table
# 5. Schedule KMS key deletion
# 6. Delete Cognito User Pool
```

## Next Steps

- Read [SECURITY.md](SECURITY.md) for security best practices
- Set up CloudFront for HTTPS and CDN
- Configure custom domain
- Implement automated backups
- Add monitoring dashboards

## Getting Help

- Check the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions
- Review [SECURITY.md](SECURITY.md) for security configurations
- Search AWS documentation for service-specific issues
- Check CloudWatch Logs for error details

## Useful Commands

```bash
# View Lambda logs
aws logs tail /aws/lambda/password-manager-prod-api --follow

# List passwords in DynamoDB (for debugging)
aws dynamodb scan --table-name PasswordManager --max-items 5

# Check KMS key status
aws kms describe-key --key-id <your-key-id>

# View Cognito users
aws cognito-idp list-users --user-pool-id <your-pool-id>

# Check API Gateway stages
aws apigateway get-stages --rest-api-id <your-api-id>

# Invalidate CloudFront cache (if using CloudFront)
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

---

**Estimated Total Setup Time**: 
- Manual: 45-60 minutes
- CloudFormation: 30-45 minutes (with manual API Gateway configuration)
- Deployment Script: 15-20 minutes (after initial setup)

**Monthly Cost**: $1-5 for personal use with AWS Free Tier
