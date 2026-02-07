// Configuration for AWS services
// These values should be replaced with your actual AWS resource values after deployment

const config = {
  // AWS Cognito Configuration
  cognito: {
    region: process.env.REACT_APP_AWS_REGION || 'us-east-1',
    userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID || 'YOUR_USER_POOL_ID',
    userPoolWebClientId: process.env.REACT_APP_COGNITO_CLIENT_ID || 'YOUR_CLIENT_ID',
  },
  
  // API Gateway Configuration
  api: {
    baseUrl: process.env.REACT_APP_API_BASE_URL || 'https://YOUR_API_GATEWAY_URL',
    endpoints: {
      passwords: '/passwords',
      decrypt: '/decrypt'
    }
  }
};

export default config;
