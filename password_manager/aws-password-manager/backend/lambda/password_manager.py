"""
AWS Lambda function for password manager CRUD operations.
Handles create, read, update, and delete operations for passwords stored in DynamoDB.
"""

import json
import os
import boto3
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
kms_client = boto3.client('kms')

# Get environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'PasswordManager')
KMS_KEY_ID = os.environ.get('KMS_KEY_ID')

# Get DynamoDB table
table = dynamodb.Table(TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal types to JSON."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def get_user_id_from_event(event):
    """Extract user ID from Cognito authorizer context."""
    try:
        # User ID is available in the authorizer context
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = claims.get('sub') or claims.get('cognito:username')
        if not user_id:
            # Fallback to direct claim
            user_id = event.get('requestContext', {}).get('authorizer', {}).get('principalId')
        return user_id
    except Exception as e:
        print(f"Error extracting user_id: {str(e)}")
        return None


def cors_response(status_code, body):
    """Generate response with CORS headers."""
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',  # Configure this to your S3 bucket URL in production
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }


def encrypt_password_with_kms(plaintext_password):
    """Encrypt password using AWS KMS."""
    try:
        response = kms_client.encrypt(
            KeyId=KMS_KEY_ID,
            Plaintext=plaintext_password.encode('utf-8')
        )
        # Return base64-encoded ciphertext
        import base64
        return base64.b64encode(response['CiphertextBlob']).decode('utf-8')
    except ClientError as e:
        print(f"KMS encryption error: {str(e)}")
        raise


def list_passwords(event):
    """List all passwords for a user."""
    user_id = get_user_id_from_event(event)
    if not user_id:
        return cors_response(401, {'error': 'Unauthorized'})
    
    try:
        response = table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id},
            ProjectionExpression='password_id,site_name,site_url,username,notes,created_at,updated_at'
        )
        
        return cors_response(200, {
            'passwords': response.get('Items', [])
        })
    except ClientError as e:
        print(f"Error listing passwords: {str(e)}")
        return cors_response(500, {'error': 'Failed to list passwords'})


def get_password(event):
    """Get a specific password by ID."""
    user_id = get_user_id_from_event(event)
    if not user_id:
        return cors_response(401, {'error': 'Unauthorized'})
    
    password_id = event.get('pathParameters', {}).get('id')
    if not password_id:
        return cors_response(400, {'error': 'Password ID is required'})
    
    try:
        response = table.get_item(
            Key={
                'user_id': user_id,
                'password_id': password_id
            }
        )
        
        item = response.get('Item')
        if not item:
            return cors_response(404, {'error': 'Password not found'})
        
        # Don't return encrypted password in list view, only when specifically requested
        return cors_response(200, item)
    except ClientError as e:
        print(f"Error getting password: {str(e)}")
        return cors_response(500, {'error': 'Failed to retrieve password'})


def create_password(event):
    """Create a new password entry."""
    user_id = get_user_id_from_event(event)
    if not user_id:
        return cors_response(401, {'error': 'Unauthorized'})
    
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return cors_response(400, {'error': 'Invalid JSON in request body'})
    
    # Validate required fields
    required_fields = ['site_name', 'username', 'password']
    for field in required_fields:
        if field not in body or not body[field]:
            return cors_response(400, {'error': f'{field} is required'})
    
    # Generate unique password ID
    import uuid
    password_id = str(uuid.uuid4())
    
    # Encrypt the password
    try:
        encrypted_password = encrypt_password_with_kms(body['password'])
    except Exception as e:
        return cors_response(500, {'error': 'Failed to encrypt password'})
    
    # Prepare item for DynamoDB
    timestamp = datetime.utcnow().isoformat()
    item = {
        'user_id': user_id,
        'password_id': password_id,
        'site_name': body['site_name'],
        'site_url': body.get('site_url', ''),
        'username': body['username'],
        'encrypted_password': encrypted_password,
        'notes': body.get('notes', ''),
        'created_at': timestamp,
        'updated_at': timestamp
    }
    
    try:
        table.put_item(Item=item)
        # Don't return encrypted password
        response_item = {k: v for k, v in item.items() if k != 'encrypted_password'}
        return cors_response(201, response_item)
    except ClientError as e:
        print(f"Error creating password: {str(e)}")
        return cors_response(500, {'error': 'Failed to create password'})


def update_password(event):
    """Update an existing password entry."""
    user_id = get_user_id_from_event(event)
    if not user_id:
        return cors_response(401, {'error': 'Unauthorized'})
    
    password_id = event.get('pathParameters', {}).get('id')
    if not password_id:
        return cors_response(400, {'error': 'Password ID is required'})
    
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return cors_response(400, {'error': 'Invalid JSON in request body'})
    
    # Verify the password exists and belongs to the user
    try:
        existing = table.get_item(
            Key={
                'user_id': user_id,
                'password_id': password_id
            }
        )
        if 'Item' not in existing:
            return cors_response(404, {'error': 'Password not found'})
    except ClientError as e:
        print(f"Error checking existing password: {str(e)}")
        return cors_response(500, {'error': 'Failed to verify password'})
    
    # Build update expression
    update_expr = "SET updated_at = :updated_at"
    expr_values = {':updated_at': datetime.utcnow().isoformat()}
    
    if 'site_name' in body:
        update_expr += ", site_name = :site_name"
        expr_values[':site_name'] = body['site_name']
    
    if 'site_url' in body:
        update_expr += ", site_url = :site_url"
        expr_values[':site_url'] = body['site_url']
    
    if 'username' in body:
        update_expr += ", username = :username"
        expr_values[':username'] = body['username']
    
    if 'notes' in body:
        update_expr += ", notes = :notes"
        expr_values[':notes'] = body['notes']
    
    if 'password' in body:
        try:
            encrypted_password = encrypt_password_with_kms(body['password'])
            update_expr += ", encrypted_password = :encrypted_password"
            expr_values[':encrypted_password'] = encrypted_password
        except Exception as e:
            return cors_response(500, {'error': 'Failed to encrypt password'})
    
    try:
        response = table.update_item(
            Key={
                'user_id': user_id,
                'password_id': password_id
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        
        # Don't return encrypted password
        item = response.get('Attributes', {})
        if 'encrypted_password' in item:
            del item['encrypted_password']
        
        return cors_response(200, item)
    except ClientError as e:
        print(f"Error updating password: {str(e)}")
        return cors_response(500, {'error': 'Failed to update password'})


def delete_password(event):
    """Delete a password entry."""
    user_id = get_user_id_from_event(event)
    if not user_id:
        return cors_response(401, {'error': 'Unauthorized'})
    
    password_id = event.get('pathParameters', {}).get('id')
    if not password_id:
        return cors_response(400, {'error': 'Password ID is required'})
    
    try:
        # Verify the password exists and belongs to the user before deleting
        existing = table.get_item(
            Key={
                'user_id': user_id,
                'password_id': password_id
            }
        )
        if 'Item' not in existing:
            return cors_response(404, {'error': 'Password not found'})
        
        table.delete_item(
            Key={
                'user_id': user_id,
                'password_id': password_id
            }
        )
        
        return cors_response(200, {'message': 'Password deleted successfully'})
    except ClientError as e:
        print(f"Error deleting password: {str(e)}")
        return cors_response(500, {'error': 'Failed to delete password'})


def lambda_handler(event, context):
    """Main Lambda handler function."""
    print(f"Event: {json.dumps(event)}")
    
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {})
    
    # Route based on HTTP method and path
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    
    try:
        if http_method == 'GET':
            if '/passwords/' in path:
                return get_password(event)
            else:
                return list_passwords(event)
        elif http_method == 'POST':
            return create_password(event)
        elif http_method == 'PUT':
            return update_password(event)
        elif http_method == 'DELETE':
            return delete_password(event)
        else:
            return cors_response(405, {'error': 'Method not allowed'})
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return cors_response(500, {'error': 'Internal server error'})
