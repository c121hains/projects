#!/bin/bash

# AWS Password Manager Deployment Script
# This script helps deploy the Lambda functions and frontend to AWS

set -e

echo "=================================="
echo "AWS Password Manager Deployment"
echo "=================================="
echo ""

# Check for required tools
command -v aws >/dev/null 2>&1 || { echo "AWS CLI is required but not installed. Aborting." >&2; exit 1; }
command -v zip >/dev/null 2>&1 || { echo "zip is required but not installed. Aborting." >&2; exit 1; }

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend/lambda"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Function to deploy Lambda function
deploy_lambda() {
    local function_name=$1
    local file_name=$2
    
    echo "Deploying Lambda function: $function_name"
    
    cd "$BACKEND_DIR"
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    
    # Copy Lambda code
    cp "$file_name" "$TEMP_DIR/"
    
    # Install dependencies if requirements.txt exists
    if [ -f requirements.txt ]; then
        echo "Installing Python dependencies..."
        pip install -r requirements.txt -t "$TEMP_DIR/" --quiet
    fi
    
    # Create zip file
    cd "$TEMP_DIR"
    zip -r function.zip . > /dev/null
    
    # Update Lambda function
    echo "Updating Lambda function code..."
    aws lambda update-function-code \
        --function-name "$function_name" \
        --zip-file fileb://function.zip \
        --no-cli-pager
    
    # Wait for update to complete
    echo "Waiting for Lambda update to complete..."
    aws lambda wait function-updated \
        --function-name "$function_name"
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    
    echo "✓ Lambda function $function_name deployed successfully"
    echo ""
}

# Function to deploy frontend
deploy_frontend() {
    local bucket_name=$1
    
    echo "Building and deploying frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Check if .env exists
    if [ ! -f .env ]; then
        echo "Warning: .env file not found in frontend directory"
        echo "Please create .env file with your AWS configuration"
        echo "See .env.example for reference"
        exit 1
    fi
    
    # Install dependencies
    echo "Installing npm dependencies..."
    npm install
    
    # Build production bundle
    echo "Building production bundle..."
    npm run build
    
    # Deploy to S3
    echo "Uploading to S3 bucket: $bucket_name"
    aws s3 sync build/ "s3://$bucket_name/" --delete --acl public-read
    
    echo "✓ Frontend deployed successfully"
    echo ""
}

# Main deployment flow
echo "What would you like to deploy?"
echo "1) Lambda functions only"
echo "2) Frontend only"
echo "3) Both Lambda and Frontend"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        read -p "Enter Password Manager Lambda function name: " pm_function
        read -p "Enter Decrypt Password Lambda function name: " decrypt_function
        
        deploy_lambda "$pm_function" "password_manager.py"
        deploy_lambda "$decrypt_function" "decrypt_password.py"
        ;;
    2)
        echo ""
        read -p "Enter S3 bucket name: " bucket_name
        
        deploy_frontend "$bucket_name"
        ;;
    3)
        echo ""
        read -p "Enter Password Manager Lambda function name: " pm_function
        read -p "Enter Decrypt Password Lambda function name: " decrypt_function
        read -p "Enter S3 bucket name: " bucket_name
        
        deploy_lambda "$pm_function" "password_manager.py"
        deploy_lambda "$decrypt_function" "decrypt_password.py"
        deploy_frontend "$bucket_name"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo "=================================="
echo "Deployment completed successfully!"
echo "=================================="
