# Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         End User                                 │
│                    (Web Browser)                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Amazon S3 (Static Website)                    │
│                    - React Web Application                       │
│                    - HTML/CSS/JavaScript                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ REST API calls
                         │ + JWT Token
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Amazon API Gateway                            │
│                    - HTTPS Endpoints                             │
│                    - Cognito Authorizer                          │
│                    - CORS Configuration                          │
│                    - Request/Response Mapping                    │
└──────────┬──────────────────────────────────┬───────────────────┘
           │                                   │
           │ Invokes                           │ Invokes
           ▼                                   ▼
┌──────────────────────────┐      ┌──────────────────────────┐
│ Lambda: password_manager │      │ Lambda: decrypt_password │
│ - List passwords         │      │ - Decrypt single password│
│ - Create password        │      │ - Return plaintext       │
│ - Update password        │      │                          │
│ - Delete password        │      │                          │
│ - Get password (encrypted)│      │                          │
└────┬──────────────┬──────┘      └────┬─────────────────────┘
     │              │                   │
     │              │ Encrypt/Decrypt   │ Decrypt
     │              │                   │
     │              ▼                   ▼
     │         ┌─────────────────────────────┐
     │         │        AWS KMS               │
     │         │ - Customer Managed Key       │
     │         │ - 256-bit AES Encryption    │
     │         │ - Automatic Key Rotation     │
     │         └─────────────────────────────┘
     │
     │ Read/Write
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Amazon DynamoDB                             │
│                      Table: PasswordManager                      │
│                                                                   │
│  Partition Key: user_id (String)                                │
│  Sort Key: password_id (String)                                  │
│                                                                   │
│  Attributes:                                                      │
│  - site_name                                                      │
│  - site_url                                                       │
│  - username                                                       │
│  - encrypted_password (KMS encrypted)                            │
│  - notes                                                          │
│  - created_at                                                     │
│  - updated_at                                                     │
│                                                                   │
│  Features:                                                        │
│  - On-demand billing                                             │
│  - Encryption at rest                                            │
│  - Point-in-time recovery                                        │
│  - Per-user data isolation                                       │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                    AWS Cognito User Pool                         │
│                    - User Management                             │
│                    - Authentication (OAuth2/OIDC)                │
│                    - MFA Support                                 │
│                    - Password Policies                           │
│                    - Email Verification                          │
│                    - JWT Token Issuance                          │
└─────────────────────────────────────────────────────────────────┘
          │
          │ Validates tokens
          └──────> API Gateway Authorizer
```

## Data Flow

### 1. User Registration Flow
```
User → S3 (React App) → Cognito User Pool
                         │
                         ├─> Send Verification Email
                         └─> Store User Credentials
```

### 2. User Login Flow
```
User → S3 (React App) → Cognito User Pool
                         │
                         ├─> Validate Credentials
                         ├─> Check MFA (if enabled)
                         └─> Issue JWT Tokens (ID, Access, Refresh)
                              │
                              └─> Store in Session (React App)
```

### 3. Create Password Flow
```
User → React App → API Gateway → Lambda (password_manager)
                      │              │
                      │              ├─> Validate JWT (via Cognito Authorizer)
                      │              ├─> Extract user_id from token
                      │              ├─> Encrypt password with KMS
                      │              └─> Store in DynamoDB
                      │                   {
                      │                     user_id: "cognito-sub-id",
                      │                     password_id: "uuid",
                      │                     site_name: "Gmail",
                      │                     encrypted_password: "base64...",
                      │                     ...
                      │                   }
                      │
                      └─> Return success response
```

### 4. List Passwords Flow
```
User → React App → API Gateway → Lambda (password_manager)
                      │              │
                      │              ├─> Validate JWT
                      │              ├─> Extract user_id
                      │              ├─> Query DynamoDB (user_id)
                      │              └─> Return list (without decrypted passwords)
                      │
                      └─> Display password list
```

### 5. View/Decrypt Password Flow
```
User → React App → API Gateway → Lambda (decrypt_password)
                      │              │
                      │              ├─> Validate JWT
                      │              ├─> Extract user_id
                      │              ├─> Get item from DynamoDB
                      │              ├─> Verify ownership (user_id match)
                      │              ├─> Decrypt with KMS
                      │              └─> Return plaintext password
                      │
                      └─> Display decrypted password temporarily
```

### 6. Update Password Flow
```
User → React App → API Gateway → Lambda (password_manager)
                      │              │
                      │              ├─> Validate JWT
                      │              ├─> Extract user_id
                      │              ├─> Verify ownership
                      │              ├─> Encrypt new password with KMS
                      │              ├─> Update DynamoDB item
                      │              └─> Update timestamp
                      │
                      └─> Return success
```

### 7. Delete Password Flow
```
User → React App → API Gateway → Lambda (password_manager)
                      │              │
                      │              ├─> Validate JWT
                      │              ├─> Extract user_id
                      │              ├─> Verify ownership
                      │              └─> Delete from DynamoDB
                      │
                      └─> Return success
```

## Security Layers

### Layer 1: Transport Security
- HTTPS for all communications
- TLS 1.2+
- Certificate validation

### Layer 2: Authentication
- AWS Cognito User Pools
- JWT tokens (ID, Access, Refresh)
- MFA support (TOTP/SMS)
- Password policies

### Layer 3: Authorization
- API Gateway Cognito Authorizer
- Per-request token validation
- User-specific data access

### Layer 4: Application Security
- Input validation
- CORS restrictions
- Rate limiting
- Request validation

### Layer 5: Data Encryption
- Passwords encrypted with AWS KMS
- Customer-managed keys
- 256-bit AES encryption
- Automatic key rotation

### Layer 6: Storage Security
- DynamoDB encryption at rest
- Per-user data isolation
- IAM policies
- Least privilege access

## Component Responsibilities

### Frontend (React on S3)
- User interface
- Client-side validation
- Cognito authentication integration
- API calls with JWT tokens
- Session management

### API Gateway
- HTTPS endpoint management
- Request routing
- JWT validation via Cognito Authorizer
- CORS handling
- Rate limiting

### Lambda Functions
- Business logic
- Password CRUD operations
- KMS encryption/decryption
- DynamoDB operations
- User authorization checks

### DynamoDB
- Persistent storage
- User data isolation
- Encrypted at rest
- High availability
- Scalability

### KMS
- Encryption key management
- Encrypt/decrypt operations
- Key rotation
- Access control

### Cognito
- User management
- Authentication
- MFA
- JWT token issuance
- Password policies

## Scalability

### Current Setup
- Suitable for: 1-1000 users
- Expected load: 10-100 requests/day per user
- Storage: Minimal (few KB per user)

### Scaling Considerations

**Lambda**
- Auto-scales with requests
- Concurrent execution limit: 1000 (default)
- Can be increased via AWS support

**DynamoDB**
- On-demand billing: Auto-scales
- Provisioned: Can configure auto-scaling
- No upper limit on storage

**API Gateway**
- Throttle: Default 10,000 requests/second
- Can be increased via AWS support

**Cognito**
- Supports millions of users
- Automatically scales

**S3**
- Unlimited storage
- High availability
- Auto-scaling

## High Availability

All AWS services used provide built-in high availability:

- **S3**: 99.99% availability, 11 9's durability
- **API Gateway**: Multi-AZ deployment
- **Lambda**: Runs across multiple AZs
- **DynamoDB**: Multi-AZ replication
- **Cognito**: Multi-AZ deployment
- **KMS**: Multi-AZ deployment

## Cost Optimization

### Free Tier Usage
- Cognito: First 50,000 MAUs
- Lambda: 1M requests + 400,000 GB-seconds
- API Gateway: 1M calls (12 months)
- DynamoDB: 25GB + 25 RCU/WCU
- S3: 5GB storage

### Beyond Free Tier
- Enable S3 lifecycle policies
- Use DynamoDB on-demand for variable load
- Monitor CloudWatch metrics
- Set up billing alerts

## Monitoring Points

- Lambda invocations and errors
- API Gateway requests and latency
- DynamoDB read/write capacity
- KMS encryption/decryption requests
- Cognito authentication attempts
- S3 bucket access

## Backup Strategy

- DynamoDB: Point-in-time recovery (35 days)
- DynamoDB: On-demand backups
- S3: Versioning enabled
- KMS: Key material cannot be deleted immediately

## Disaster Recovery

- RTO (Recovery Time Objective): < 1 hour
- RPO (Recovery Point Objective): < 5 minutes (DynamoDB PITR)
- Multi-region: Can be deployed in multiple regions
- Backup restoration: DynamoDB backups can be restored to new table
