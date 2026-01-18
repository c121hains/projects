# AWS Secure Password Manager

A secure, ultra-low-cost password manager built on AWS infrastructure with enterprise-grade security features.

![Password Manager Architecture](docs/architecture-diagram.png)

## Features

✅ **Secure Authentication**
- AWS Cognito User Pools for user management
- Username/password authentication
- Multi-factor authentication (MFA) support
- Password policies and complexity requirements
- Email verification

✅ **End-to-End Encryption**
- Passwords encrypted with AWS KMS (256-bit encryption)
- Customer-managed encryption keys
- Separate encryption/decryption Lambda functions
- Zero-knowledge architecture (passwords only decrypted on-demand)

✅ **Full CRUD Operations**
- Create, Read, Update, Delete passwords
- Organize passwords by site name, URL, username
- Add notes for additional context
- Password generator included

✅ **Secure Storage**
- Amazon DynamoDB for scalable, encrypted storage
- Per-user data isolation
- Automatic timestamps for audit trails

✅ **Modern Web Interface**
- Responsive React web application
- Clean, intuitive UI
- Mobile-friendly design
- Hosted on Amazon S3 with static website hosting

✅ **Production-Ready**
- RESTful API through Amazon API Gateway
- HTTPS endpoints with Cognito authorization
- CORS support
- Comprehensive error handling
- CloudWatch logging

## Architecture

```
┌─────────────────┐
│   React Web App │ (S3 Static Hosting)
│   (Frontend)    │
└────────┬────────┘
         │ HTTPS
         │
    ┌────▼─────────────────┐
    │   API Gateway        │ (HTTPS Endpoints + Cognito Auth)
    └────┬─────────────────┘
         │
         │ Invokes
         │
    ┌────▼──────────────────┐
    │  Lambda Functions     │
    │  - Password CRUD      │
    │  - Decrypt Password   │
    └────┬──────────┬───────┘
         │          │
         │          │ Encrypt/Decrypt
         │          │
    ┌────▼────┐  ┌──▼──────┐
    │DynamoDB │  │AWS KMS  │
    │(Storage)│  │(Crypto) │
    └─────────┘  └─────────┘
         │
    ┌────▼──────────┐
    │ AWS Cognito   │
    │ (Auth/Users)  │
    └───────────────┘
```

## Technology Stack

### Backend
- **AWS Lambda**: Serverless compute for API logic
- **Python 3.11+**: Lambda runtime
- **boto3**: AWS SDK for Python
- **Amazon DynamoDB**: NoSQL database for password storage
- **AWS KMS**: Key Management Service for encryption
- **Amazon API Gateway**: RESTful API endpoints
- **AWS Cognito**: User authentication and authorization

### Frontend
- **React 18**: Modern JavaScript UI framework
- **amazon-cognito-identity-js**: Cognito authentication SDK
- **axios**: HTTP client for API calls
- **CSS3**: Responsive styling

## Project Structure

```
aws-password-manager/
├── backend/
│   └── lambda/
│       ├── password_manager.py      # Main CRUD Lambda function
│       ├── decrypt_password.py      # Password decryption Lambda
│       └── requirements.txt         # Python dependencies
│
├── frontend/
│   ├── public/
│   │   └── index.html              # HTML template
│   ├── src/
│   │   ├── components/             # React components
│   │   │   ├── Login.js
│   │   │   ├── Register.js
│   │   │   ├── Dashboard.js
│   │   │   ├── PasswordForm.js
│   │   │   └── PasswordView.js
│   │   ├── App.js                  # Main app component
│   │   ├── App.css                 # Styling
│   │   ├── config.js               # AWS configuration
│   │   ├── authService.js          # Cognito authentication
│   │   ├── apiService.js           # API client
│   │   └── index.js                # Entry point
│   ├── package.json                # Dependencies
│   └── .env.example                # Environment template
│
├── docs/
│   ├── DEPLOYMENT_GUIDE.md         # Comprehensive deployment guide
│   └── SECURITY.md                 # Security best practices
│
└── README.md                       # This file
```

## Quick Start

### Prerequisites

- AWS account with appropriate permissions
- AWS CLI installed and configured
- Node.js 18+ and npm
- Python 3.9+

### Deployment Steps

1. **Follow the comprehensive deployment guide**: See [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)

2. **Quick summary**:
   - Create Cognito User Pool
   - Create DynamoDB table
   - Create KMS encryption key
   - Deploy Lambda functions
   - Configure API Gateway
   - Deploy React app to S3

3. **Configure frontend**:
   ```bash
   cd frontend
   cp .env.example .env
   # Edit .env with your AWS resource IDs
   npm install
   npm run build
   ```

4. **Deploy to S3**:
   ```bash
   aws s3 sync build/ s3://your-bucket-name/
   ```

5. **Access your app**:
   - Navigate to your S3 website URL
   - Register a new account
   - Start managing passwords securely!

## Cost Estimate

Designed for ultra-low cost operation:

| Service | Free Tier | Expected Cost |
|---------|-----------|---------------|
| Cognito | 50,000 MAUs | $0 |
| Lambda | 1M requests/month | $0 |
| API Gateway | 1M calls (12 months) | $0 |
| DynamoDB | 25GB + 25 RCU/WCU | $0 |
| KMS | - | $1/month |
| S3 | 5GB + requests | $0.50/month |

**Total Monthly Cost**: $1-5 for personal use

## Security Features

### Authentication & Authorization
- ✅ AWS Cognito with OAuth2/OIDC flows
- ✅ JWT token-based authentication
- ✅ Optional MFA support
- ✅ Password complexity policies
- ✅ Email verification

### Encryption
- ✅ AWS KMS customer-managed keys
- ✅ 256-bit AES encryption
- ✅ Passwords encrypted at rest
- ✅ Passwords only decrypted on explicit request
- ✅ HTTPS for all communications

### Access Control
- ✅ Per-user data isolation in DynamoDB
- ✅ API Gateway Cognito authorizers
- ✅ IAM roles with least privilege
- ✅ CORS protection

### Audit & Monitoring
- ✅ CloudWatch logs for all operations
- ✅ Timestamps for all password operations
- ✅ API Gateway access logs

See [SECURITY.md](docs/SECURITY.md) for more details.

## API Endpoints

### Authentication
- Handled by AWS Cognito (register, login, logout, verify)

### Password Management
- `GET /passwords` - List all passwords
- `GET /passwords/{id}` - Get password details (without decrypted value)
- `POST /passwords` - Create new password
- `PUT /passwords/{id}` - Update password
- `DELETE /passwords/{id}` - Delete password
- `GET /decrypt/{id}` - Decrypt and retrieve password value

All endpoints require Bearer token authentication.

## Development

### Local Frontend Development

```bash
cd frontend
npm install
npm start
```

Access at `http://localhost:3000`

### Testing Lambda Functions Locally

```bash
cd backend/lambda
pip install -r requirements.txt
# Set environment variables
export DYNAMODB_TABLE=PasswordManager
export KMS_KEY_ID=your-key-id
# Run tests or invoke functions
python -c "from password_manager import lambda_handler; print(lambda_handler({'httpMethod': 'GET'}, {}))"
```

## Troubleshooting

### Common Issues

**Cannot sign in**
- Verify Cognito User Pool ID and Client ID in `.env`
- Confirm email is verified
- Check browser console for errors

**API calls fail**
- Verify API Gateway URL is correct
- Check Cognito authorizer is configured
- Ensure Lambda has correct IAM permissions

**CORS errors**
- Enable CORS on all API Gateway resources
- Update Lambda response headers
- Clear browser cache

See [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for more troubleshooting tips.

## Roadmap

- [ ] Password strength indicator
- [ ] Password history tracking
- [ ] Secure password sharing
- [ ] Browser extension
- [ ] Mobile app (React Native)
- [ ] Two-factor authentication tokens
- [ ] Password breach checking
- [ ] Export/Import functionality
- [ ] CloudFormation/Terraform templates
- [ ] CI/CD pipeline

## Contributing

This is a reference implementation for educational purposes. Feel free to fork and customize for your needs.

## License

MIT License - See LICENSE file for details

## Disclaimer

This is provided as-is for educational and personal use. While it implements security best practices, use at your own risk. Always review code before deploying to production and ensure compliance with your security requirements.

## Support

For issues, questions, or contributions, please open an issue in the repository.

---

**Built with ❤️ using AWS serverless technologies**
