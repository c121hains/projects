# Security Best Practices for AWS Password Manager

This document outlines security considerations and best practices for deploying and maintaining the AWS Secure Password Manager.

## Table of Contents

1. [Authentication Security](#authentication-security)
2. [Encryption and Key Management](#encryption-and-key-management)
3. [Network Security](#network-security)
4. [Access Control](#access-control)
5. [Monitoring and Auditing](#monitoring-and-auditing)
6. [Data Protection](#data-protection)
7. [Operational Security](#operational-security)
8. [Compliance Considerations](#compliance-considerations)

---

## Authentication Security

### AWS Cognito Configuration

#### Password Policies
Configure strong password requirements in Cognito User Pool:

```
Minimum length: 12 characters (recommended)
Require uppercase: Yes
Require lowercase: Yes
Require numbers: Yes
Require special characters: Yes
Temporary password validity: 1 day
```

#### Multi-Factor Authentication (MFA)
Enable MFA for enhanced security:

1. **SMS MFA**: Basic second factor using phone numbers
2. **TOTP MFA**: Time-based one-time passwords (Google Authenticator, Authy)
3. **Recommended**: Set MFA to "Optional" initially, then "Required" for production

Configuration:
```
Cognito User Pool > Sign-in experience > Multi-factor authentication
- Select: Required or Optional
- MFA methods: TOTP and SMS
```

#### Account Recovery
Configure secure account recovery:

```
- Recovery method: Email only (more secure than SMS)
- Verification message: Customize with your branding
- Code validity: 24 hours (default)
```

#### Advanced Security Features
Enable AWS Cognito Advanced Security:

1. **Adaptive Authentication**: Automatically challenges suspicious sign-in attempts
2. **Compromised Credentials Protection**: Blocks known compromised passwords
3. **Risk-Based Authentication**: Requires additional verification for high-risk sign-ins

### Session Management

#### Token Configuration
Configure appropriate token expiration:

```javascript
// In Cognito User Pool App Client settings:
Refresh token expiration: 30 days
Access token expiration: 1 hour
ID token expiration: 1 hour
```

#### Secure Token Storage
Frontend best practices:

```javascript
// Never store tokens in localStorage (vulnerable to XSS)
// Use Cognito session management (sessionStorage)
// Implement auto-logout on inactivity
```

### Frontend Security

#### Input Validation
```javascript
// Validate all user inputs
// Sanitize before sending to API
// Use proper React patterns to prevent XSS
```

#### Content Security Policy
Add CSP headers to S3-hosted site:

```http
Content-Security-Policy: 
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://cognito-identity.amazonaws.com;
  style-src 'self' 'unsafe-inline';
  connect-src 'self' https://*.execute-api.*.amazonaws.com https://cognito-idp.*.amazonaws.com;
  img-src 'self' data:;
```

---

## Encryption and Key Management

### AWS KMS Configuration

#### Customer Managed Keys
Always use customer-managed KMS keys (CMK) instead of AWS-managed keys:

**Benefits**:
- Full control over key policies
- Ability to disable/enable keys
- Audit trail of key usage
- Key rotation control

#### Key Policy Best Practices

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow Lambda to use the key",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:role/password-manager-lambda-role"
      },
      "Action": [
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Allow CloudWatch Logs",
      "Effect": "Allow",
      "Principal": {
        "Service": "logs.amazonaws.com"
      },
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "*",
      "Condition": {
        "ArnLike": {
          "kms:EncryptionContext:aws:logs:arn": "arn:aws:logs:*:ACCOUNT_ID:*"
        }
      }
    }
  ]
}
```

#### Key Rotation

Enable automatic key rotation:
```
AWS KMS > Customer managed keys > Select key > Key rotation
- Enable automatic rotation: Yes (rotates every year)
```

Or implement manual rotation strategy:
- Rotate keys annually
- Update Lambda environment variables
- Maintain old keys for decryption of existing data
- Re-encrypt data with new keys over time

#### Key Usage Monitoring

Monitor KMS key usage:
```
CloudWatch > Metrics > KMS
- Monitor: NumberOfDecrypts, NumberOfEncrypts
- Set alarms for unusual activity
```

### Encryption Implementation

#### Password Encryption Flow
```python
# Encryption (when saving password)
plaintext_password → KMS Encrypt → Base64 encode → Store in DynamoDB

# Decryption (when viewing password)
DynamoDB encrypted value → Base64 decode → KMS Decrypt → plaintext_password
```

#### Additional Encryption Layers

Consider additional encryption for sensitive notes:
```python
# Encrypt notes field as well
notes = encrypt_with_kms(sensitive_notes)
```

---

## Network Security

### API Gateway Security

#### HTTPS Only
Ensure all traffic uses HTTPS:
- API Gateway enforces HTTPS by default
- Never expose HTTP endpoints

#### CORS Configuration

Restrict CORS to your domain only:

```javascript
// In production, replace '*' with your domain
headers: {
  'Access-Control-Allow-Origin': 'https://your-domain.com',
  'Access-Control-Allow-Credentials': 'true',
  'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type,Authorization'
}
```

#### API Gateway Authorizers

Verify Cognito authorizer is configured on ALL endpoints:
```
API Gateway > Resources > Each Method > Method Request
- Authorization: cognito-authorizer
- API Key Required: false (using Cognito instead)
```

#### Rate Limiting and Throttling

Implement usage plans:
```
API Gateway > Usage Plans > Create
- Throttle: 100 requests per second
- Burst: 200 requests
- Quota: 10,000 requests per day
```

#### Request Validation

Enable request validation in API Gateway:
```json
// Request body validation model
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "site_name": {"type": "string", "maxLength": 128},
    "username": {"type": "string", "maxLength": 128},
    "password": {"type": "string", "maxLength": 256}
  },
  "required": ["site_name", "username", "password"]
}
```

### CloudFront Distribution (Recommended)

Add CloudFront in front of S3 for additional security:

**Benefits**:
- DDoS protection
- SSL/TLS certificates
- Geographic restrictions
- WAF integration
- Origin access control

**Configuration**:
```
CloudFront > Create Distribution
- Origin: S3 bucket
- Viewer Protocol Policy: Redirect HTTP to HTTPS
- Allowed HTTP Methods: GET, HEAD, OPTIONS
- Compress Objects: Yes
- AWS WAF: Enable (optional)
```

### VPC Configuration (Optional)

For enterprise deployments, place Lambda in VPC:

**Benefits**:
- Network isolation
- Private subnet access
- Network ACLs
- VPC Flow Logs

**Considerations**:
- Requires NAT Gateway for internet access (additional cost)
- Adds latency
- More complex configuration

---

## Access Control

### IAM Policies

#### Lambda Execution Role
Implement least privilege:

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
      "Resource": "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/PasswordManager",
      "Condition": {
        "ForAllValues:StringEquals": {
          "dynamodb:LeadingKeys": ["${cognito-identity.amazonaws.com:sub}"]
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:REGION:ACCOUNT_ID:key/KEY_ID"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:REGION:ACCOUNT_ID:log-group:/aws/lambda/*"
    }
  ]
}
```

#### DynamoDB Table Policies

Enable point-in-time recovery:
```
DynamoDB > Tables > PasswordManager > Backups
- Point-in-time recovery: Enabled
```

### Resource Tagging

Tag all resources for better governance:
```
Project: password-manager
Environment: production
Compliance: pci-dss (if applicable)
Owner: your-team
CostCenter: your-cost-center
```

---

## Monitoring and Auditing

### CloudWatch Logging

#### Lambda Logs
Ensure all Lambda functions log appropriately:

```python
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Processing request for user: {user_id}")
    # Never log passwords or sensitive data
    logger.info(f"Operation: {operation}, Resource: {resource_id}")
```

#### API Gateway Access Logs

Enable access logs:
```
API Gateway > Stages > prod > Logs/Tracing
- Enable CloudWatch Logs: Yes
- Log level: INFO
- Log full requests/responses: No (contains sensitive data)
- Access logging: Yes
- Log format: JSON
```

### CloudWatch Alarms

Set up critical alarms:

```
1. Lambda Errors
   - Metric: Errors
   - Threshold: > 5 in 5 minutes
   - Action: SNS notification

2. Lambda Throttles
   - Metric: Throttles
   - Threshold: > 1
   - Action: SNS notification

3. API Gateway 4xx Errors
   - Metric: 4XXError
   - Threshold: > 100 in 5 minutes
   - Action: SNS notification

4. API Gateway 5xx Errors
   - Metric: 5XXError
   - Threshold: > 10 in 5 minutes
   - Action: SNS notification

5. DynamoDB Throttles
   - Metric: UserErrors
   - Threshold: > 10
   - Action: SNS notification

6. KMS Decrypt Failures
   - Metric: Custom metric from Lambda
   - Threshold: > 5 in 5 minutes
   - Action: SNS notification
```

### AWS CloudTrail

Enable CloudTrail for audit trail:
```
CloudTrail > Create trail
- Trail name: password-manager-audit
- Management events: All
- Data events: S3 (read/write), Lambda (invoke)
- Insights: Enable
- Encrypt log files: Yes (KMS)
```

### GuardDuty

Enable GuardDuty for threat detection:
```
GuardDuty > Get Started
- Automatically monitors CloudTrail, VPC Flow Logs, DNS logs
- Alerts on suspicious activity
```

---

## Data Protection

### DynamoDB Security

#### Encryption at Rest
Enable encryption:
```
DynamoDB > Tables > PasswordManager > Additional settings
- Encryption: AWS managed key or Customer managed key (KMS)
```

#### Backup Strategy

1. **Point-in-Time Recovery**: Continuous backups
2. **On-Demand Backups**: Manual backups before major changes
3. **AWS Backup**: Centralized backup management

```
AWS Backup > Create backup plan
- Frequency: Daily
- Retention: 30 days
- Vault: password-manager-backups
- Vault encryption: KMS
```

#### Data Retention

Implement TTL for deleted items:
```python
# Add TTL attribute to items when marking as deleted
import time
ttl = int(time.time()) + (90 * 24 * 60 * 60)  # 90 days
```

### S3 Security

#### Bucket Policies
Restrict access appropriately:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-bucket/*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": ["YOUR_IP_RANGES"]
        }
      }
    }
  ]
}
```

#### Versioning and Lifecycle

Enable versioning:
```
S3 > Bucket > Properties > Bucket Versioning: Enable
```

Configure lifecycle rules:
```
S3 > Bucket > Management > Lifecycle rules
- Transition to Glacier after 90 days
- Delete after 365 days
```

#### Access Logging

Enable S3 access logs:
```
S3 > Bucket > Properties > Server access logging
- Target bucket: logs-bucket
- Target prefix: s3-access/
```

---

## Operational Security

### Secrets Management

Never hardcode secrets:
```python
# ❌ Bad
API_KEY = "abc123xyz"

# ✅ Good
API_KEY = os.environ.get('API_KEY')

# ✅ Better - use AWS Secrets Manager
import boto3
secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='my-secret')
```

### Environment Separation

Maintain separate environments:
```
- Development: dev-password-manager-*
- Staging: staging-password-manager-*
- Production: prod-password-manager-*
```

### Deployment Security

1. **Infrastructure as Code**: Use CloudFormation or Terraform
2. **CI/CD Pipeline**: Automate deployments with CodePipeline
3. **Code Review**: Require reviews before merging
4. **Automated Testing**: Unit tests, integration tests
5. **Security Scanning**: Use tools like:
   - AWS Inspector
   - Third-party SAST/DAST tools
   - Dependency vulnerability scanning

### Incident Response Plan

Prepare for security incidents:

1. **Detection**: CloudWatch alarms, GuardDuty alerts
2. **Containment**: 
   - Disable compromised IAM credentials
   - Rotate KMS keys
   - Block suspicious IPs in WAF
3. **Investigation**: Review CloudTrail logs
4. **Remediation**: Patch vulnerabilities, update code
5. **Recovery**: Restore from backups if needed
6. **Post-Incident**: Document lessons learned

---

## Compliance Considerations

### GDPR Compliance

If storing EU citizen data:
- ✅ Obtain explicit consent
- ✅ Allow data export (implement export function)
- ✅ Allow data deletion (already implemented)
- ✅ Implement data retention policies
- ✅ Maintain audit logs
- ✅ Document data processing activities

### PCI DSS Compliance

If storing payment card data (not recommended):
- Implement additional controls
- Regular security assessments
- Network segmentation
- Consider using AWS PCI DSS compliant services

### HIPAA Compliance

If storing health data:
- Sign AWS Business Associate Agreement (BAA)
- Use HIPAA-eligible services only
- Implement additional access controls
- Enhanced audit logging

### SOC 2 Compliance

For business use:
- Implement security controls from Trust Service Criteria
- Regular security assessments
- Incident response procedures
- Vendor risk management

---

## Security Checklist

Use this checklist before going to production:

### Authentication & Authorization
- [ ] MFA enabled on Cognito
- [ ] Strong password policy configured
- [ ] Account lockout policy enabled
- [ ] Cognito authorizer on all API endpoints
- [ ] Token expiration configured appropriately

### Encryption
- [ ] KMS customer-managed key created
- [ ] Key rotation enabled
- [ ] Passwords encrypted before storage
- [ ] HTTPS enforced on all endpoints
- [ ] DynamoDB encryption at rest enabled

### Access Control
- [ ] Lambda IAM role follows least privilege
- [ ] DynamoDB table has proper IAM policies
- [ ] S3 bucket policy restricts access
- [ ] API Gateway throttling configured

### Monitoring
- [ ] CloudWatch logs enabled for Lambda
- [ ] API Gateway access logs enabled
- [ ] CloudTrail enabled
- [ ] Critical alarms configured
- [ ] SNS notifications set up

### Data Protection
- [ ] DynamoDB point-in-time recovery enabled
- [ ] Regular backups configured
- [ ] Data retention policy implemented
- [ ] S3 versioning enabled

### Network Security
- [ ] CORS restricted to specific domain
- [ ] Rate limiting configured
- [ ] CloudFront distribution created (optional)
- [ ] WAF rules configured (optional)

### Operational
- [ ] Secrets stored in environment variables or Secrets Manager
- [ ] No hardcoded credentials in code
- [ ] Code reviewed before deployment
- [ ] Incident response plan documented
- [ ] Regular security assessments scheduled

---

## Resources

- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/)
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)

---

**Remember**: Security is an ongoing process, not a one-time setup. Regularly review and update your security posture.
