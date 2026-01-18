# Deployment Configuration Checklist

Use this checklist to track your AWS resource configuration values during deployment.

## AWS Account Information

- [ ] AWS Account ID: `____________________________`
- [ ] AWS Region: `____________________________`
- [ ] AWS CLI Profile: `____________________________`

## 1. AWS Cognito User Pool

### Configuration Steps Completed
- [ ] User Pool created
- [ ] Password policy configured (12+ chars, complexity)
- [ ] MFA configured (Optional/Required/Off)
- [ ] Email verification enabled
- [ ] App client created (no client secret)
- [ ] Authentication flows enabled (USER_PASSWORD_AUTH, REFRESH_TOKEN_AUTH)

### Values to Save
- [ ] User Pool ID: `____________________________`
- [ ] User Pool ARN: `____________________________`
- [ ] App Client ID: `____________________________`
- [ ] User Pool Region: `____________________________`

## 2. Amazon DynamoDB

### Configuration Steps Completed
- [ ] Table created with name: `PasswordManager`
- [ ] Partition key: `user_id` (String)
- [ ] Sort key: `password_id` (String)
- [ ] Billing mode: Pay-per-request OR Provisioned
- [ ] Encryption at rest enabled
- [ ] Point-in-time recovery enabled

### Values to Save
- [ ] Table Name: `____________________________`
- [ ] Table ARN: `____________________________`

## 3. AWS KMS

### Configuration Steps Completed
- [ ] Customer-managed key created
- [ ] Key alias: `password-manager-encryption-key`
- [ ] Key rotation enabled
- [ ] Key policy allows Lambda role
- [ ] Key administrators configured

### Values to Save
- [ ] Key ID: `____________________________`
- [ ] Key ARN: `____________________________`
- [ ] Key Alias: `____________________________`

## 4. IAM Role for Lambda

### Configuration Steps Completed
- [ ] Role created: `password-manager-lambda-role`
- [ ] AWSLambdaBasicExecutionRole attached
- [ ] Custom policy for DynamoDB access created
- [ ] Custom policy for KMS access created
- [ ] Trust policy allows Lambda service

### Values to Save
- [ ] Role Name: `____________________________`
- [ ] Role ARN: `____________________________`

### IAM Policy Checklist
- [ ] DynamoDB permissions (GetItem, PutItem, UpdateItem, DeleteItem, Query)
- [ ] KMS permissions (Encrypt, Decrypt, GenerateDataKey)
- [ ] CloudWatch Logs permissions

## 5. AWS Lambda Functions

### Password Manager Function
- [ ] Function created: `password-manager-api`
- [ ] Runtime: Python 3.11 or 3.12
- [ ] Handler: `password_manager.lambda_handler`
- [ ] Role: `password-manager-lambda-role`
- [ ] Timeout: 30 seconds
- [ ] Memory: 256 MB
- [ ] Code uploaded
- [ ] Environment variables set

### Environment Variables
- [ ] `DYNAMODB_TABLE`: `____________________________`
- [ ] `KMS_KEY_ID`: `____________________________`

### Values to Save
- [ ] Function Name: `____________________________`
- [ ] Function ARN: `____________________________`

### Decrypt Password Function
- [ ] Function created: `decrypt-password-api`
- [ ] Runtime: Python 3.11 or 3.12
- [ ] Handler: `decrypt_password.lambda_handler`
- [ ] Role: `password-manager-lambda-role`
- [ ] Timeout: 30 seconds
- [ ] Memory: 256 MB
- [ ] Code uploaded
- [ ] Environment variables set

### Environment Variables
- [ ] `DYNAMODB_TABLE`: `____________________________`
- [ ] `KMS_KEY_ID`: `____________________________`

### Values to Save
- [ ] Function Name: `____________________________`
- [ ] Function ARN: `____________________________`

## 6. Amazon API Gateway

### Configuration Steps Completed
- [ ] REST API created: `password-manager-api`
- [ ] Cognito authorizer created
- [ ] Resources created: `/passwords`, `/passwords/{id}`, `/decrypt/{id}`
- [ ] Methods created and integrated with Lambda
- [ ] CORS enabled on all resources
- [ ] Cognito authorizer enabled on all methods (except OPTIONS)
- [ ] Lambda permissions granted
- [ ] API deployed to stage: `prod`

### Resources and Methods Checklist
- [ ] `GET /passwords` → password-manager-api
- [ ] `POST /passwords` → password-manager-api
- [ ] `GET /passwords/{id}` → password-manager-api
- [ ] `PUT /passwords/{id}` → password-manager-api
- [ ] `DELETE /passwords/{id}` → password-manager-api
- [ ] `GET /decrypt/{id}` → decrypt-password-api
- [ ] OPTIONS methods for CORS

### Values to Save
- [ ] API ID: `____________________________`
- [ ] API Invoke URL: `____________________________`
- [ ] Stage Name: `prod`
- [ ] Full API URL: `https://______.execute-api.______.amazonaws.com/prod`

## 7. Amazon S3 (Frontend)

### Configuration Steps Completed
- [ ] Bucket created (globally unique name)
- [ ] Static website hosting enabled
- [ ] Index document: `index.html`
- [ ] Error document: `index.html`
- [ ] Public access enabled (for static site)
- [ ] Bucket policy configured for public read
- [ ] Versioning enabled (optional)

### Values to Save
- [ ] Bucket Name: `____________________________`
- [ ] Bucket Website URL: `____________________________`
- [ ] Bucket Region: `____________________________`

## 8. Frontend Configuration

### Configuration Steps Completed
- [ ] Node.js and npm installed
- [ ] Frontend dependencies installed (`npm install`)
- [ ] `.env` file created from `.env.example`
- [ ] Environment variables configured
- [ ] Production build created (`npm run build`)
- [ ] Files uploaded to S3 bucket

### Environment Variables in .env
```
REACT_APP_AWS_REGION=____________________________
REACT_APP_COGNITO_USER_POOL_ID=____________________________
REACT_APP_COGNITO_CLIENT_ID=____________________________
REACT_APP_API_BASE_URL=____________________________
```

## 9. Testing Checklist

### User Registration & Authentication
- [ ] Can access frontend URL
- [ ] Registration form loads
- [ ] Can register new user with email
- [ ] Verification email received
- [ ] Can verify email with code
- [ ] Can sign in with credentials
- [ ] Dashboard loads after sign in
- [ ] Can sign out

### Password Management
- [ ] Can create new password
- [ ] Password appears in dashboard
- [ ] Can view password details
- [ ] Can decrypt password
- [ ] Decrypted password is correct
- [ ] Can copy password to clipboard
- [ ] Can edit password
- [ ] Changes are saved
- [ ] Can delete password
- [ ] Deleted password removed from list

### Security
- [ ] Cannot access API without authentication
- [ ] Cannot access dashboard without login
- [ ] Logout redirects to login
- [ ] Cannot access other users' passwords
- [ ] Passwords encrypted in DynamoDB (check console)
- [ ] HTTPS enforced (no HTTP access)

### UI/UX
- [ ] UI is responsive on mobile
- [ ] All buttons work
- [ ] Forms validate input
- [ ] Error messages display
- [ ] Loading states display
- [ ] Password generator works

## 10. Security Hardening

### Post-Deployment Security
- [ ] CORS restricted to your domain (update Lambda functions)
- [ ] MFA enabled on Cognito (if not already)
- [ ] API Gateway throttling configured
- [ ] CloudWatch alarms set up
- [ ] CloudTrail enabled for audit logging
- [ ] S3 bucket policy restricted (if possible)
- [ ] IAM roles reviewed (least privilege)
- [ ] Secrets not in code (environment variables used)

## 11. Monitoring Setup

### CloudWatch Configuration
- [ ] Lambda logs enabled
- [ ] API Gateway access logs enabled
- [ ] CloudTrail enabled
- [ ] Alarms created:
  - [ ] Lambda errors
  - [ ] Lambda throttles
  - [ ] API Gateway 4xx errors
  - [ ] API Gateway 5xx errors
  - [ ] DynamoDB throttles
- [ ] SNS topic for notifications
- [ ] Email subscribed to SNS topic

## 12. Backup Configuration

### Backup Setup
- [ ] DynamoDB point-in-time recovery enabled
- [ ] S3 versioning enabled
- [ ] AWS Backup plan created (optional)
- [ ] Backup retention period set
- [ ] Backup testing performed

## 13. Cost Management

### Cost Optimization
- [ ] AWS Budget created with alert
- [ ] Cost alerts configured (email)
- [ ] Billing dashboard reviewed
- [ ] Free tier usage monitored
- [ ] Unused resources cleaned up

### Budget Details
- [ ] Monthly budget limit: $____
- [ ] Alert threshold: ____%
- [ ] Alert email: `____________________________`

## 14. Documentation

### Documentation Completed
- [ ] All AWS resource IDs documented
- [ ] Deployment notes saved
- [ ] Configuration changes documented
- [ ] Custom modifications noted
- [ ] Troubleshooting notes recorded

## 15. Optional Enhancements

### CloudFront (Optional)
- [ ] CloudFront distribution created
- [ ] Origin set to S3 bucket
- [ ] HTTPS only enforced
- [ ] Custom domain configured
- [ ] SSL certificate added
- [ ] API Gateway CORS updated for CloudFront domain

### Custom Domain (Optional)
- [ ] Domain registered or available
- [ ] Route 53 hosted zone created
- [ ] SSL certificate requested (ACM)
- [ ] CloudFront/S3 configured with domain
- [ ] API Gateway custom domain configured

### WAF (Optional)
- [ ] AWS WAF enabled on API Gateway
- [ ] Rate limiting rules configured
- [ ] IP blacklist/whitelist configured
- [ ] SQL injection protection enabled
- [ ] XSS protection enabled

## Quick Reference Card

Cut this out and keep it handy:

```
┌─────────────────────────────────────────────────┐
│     AWS PASSWORD MANAGER - QUICK REFERENCE      │
├─────────────────────────────────────────────────┤
│ Cognito User Pool ID:                          │
│ _______________________________________________ │
│                                                 │
│ Cognito Client ID:                             │
│ _______________________________________________ │
│                                                 │
│ API Gateway URL:                               │
│ _______________________________________________ │
│                                                 │
│ Frontend URL:                                  │
│ _______________________________________________ │
│                                                 │
│ KMS Key ID:                                    │
│ _______________________________________________ │
│                                                 │
│ DynamoDB Table:                                │
│ _______________________________________________ │
│                                                 │
│ Lambda Function (CRUD):                        │
│ _______________________________________________ │
│                                                 │
│ Lambda Function (Decrypt):                     │
│ _______________________________________________ │
│                                                 │
│ S3 Bucket:                                     │
│ _______________________________________________ │
└─────────────────────────────────────────────────┘
```

## Deployment Status

- [ ] **Phase 1**: AWS Resources Created
- [ ] **Phase 2**: Lambda Functions Deployed
- [ ] **Phase 3**: API Gateway Configured
- [ ] **Phase 4**: Frontend Deployed
- [ ] **Phase 5**: Testing Completed
- [ ] **Phase 6**: Security Hardened
- [ ] **Phase 7**: Monitoring Enabled
- [ ] **Phase 8**: Backups Configured

---

**Deployment Date**: ____________________

**Deployed By**: ____________________

**Notes**:
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
