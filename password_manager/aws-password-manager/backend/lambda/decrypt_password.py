"""
AWS Lambda function for decrypting passwords using KMS.
This function is called separately to decrypt passwords on-demand.
"""

import json
import os
import base64
import boto3
from botocore.exceptions import ClientError

# Initialize KMS client
kms_client = boto3.client('kms')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'PasswordManager')
KMS_KEY_ID = os.environ.get('KMS_KEY_ID')

# Get DynamoDB table
table = dynamodb.Table(TABLE_NAME)


def cors_response(status_code, body):
    """Generate response with CORS headers.
    
    IMPORTANT: In production, replace '*' with your specific S3 bucket URL or CloudFront domain.
    Example: 'https://your-bucket-name.s3-website-us-east-1.amazonaws.com'
    or 'https://your-domain.com'
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',  # TODO: Replace with your domain in production
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }


def get_user_id_from_event(event):
    """Extract user ID from Cognito authorizer context."""
    try:
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = claims.get('sub') or claims.get('cognito:username')
        if not user_id:
            user_id = event.get('requestContext', {}).get('authorizer', {}).get('principalId')
        return user_id
    except Exception as e:
        print(f"Error extracting user_id: {str(e)}")
        return None


def decrypt_password_with_kms(encrypted_password):
    """Decrypt password using AWS KMS."""
    try:
        # Decode base64 ciphertext
        ciphertext_blob = base64.b64decode(encrypted_password)
        
        # Decrypt with KMS
        response = kms_client.decrypt(
            CiphertextBlob=ciphertext_blob
        )
        
        # Return decrypted plaintext
        return response['Plaintext'].decode('utf-8')
    except ClientError as e:
        print(f"KMS decryption error: {str(e)}")
        raise
    except Exception as e:
        print(f"Decryption error: {str(e)}")
        raise


def lambda_handler(event, context):
    """Main Lambda handler for password decryption."""
    print(f"Event: {json.dumps(event)}")
    
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {})
    
    # Get user ID from Cognito
    user_id = get_user_id_from_event(event)
    if not user_id:
        return cors_response(401, {'error': 'Unauthorized'})
    
    # Get password ID from path
    password_id = event.get('pathParameters', {}).get('id')
    if not password_id:
        return cors_response(400, {'error': 'Password ID is required'})
    
    try:
        # Retrieve the password from DynamoDB
        response = table.get_item(
            Key={
                'user_id': user_id,
                'password_id': password_id
            }
        )
        
        item = response.get('Item')
        if not item:
            return cors_response(404, {'error': 'Password not found'})
        
        # Decrypt the password
        encrypted_password = item.get('encrypted_password')
        if not encrypted_password:
            return cors_response(500, {'error': 'No encrypted password found'})
        
        try:
            decrypted_password = decrypt_password_with_kms(encrypted_password)
        except Exception as e:
            print(f"Failed to decrypt password: {str(e)}")
            return cors_response(500, {'error': 'Failed to decrypt password'})
        
        return cors_response(200, {
            'password_id': password_id,
            'decrypted_password': decrypted_password
        })
        
    except ClientError as e:
        print(f"DynamoDB error: {str(e)}")
        return cors_response(500, {'error': 'Failed to retrieve password'})
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return cors_response(500, {'error': 'Internal server error'})
