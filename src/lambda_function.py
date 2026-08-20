# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
Order Processing Lambda function for AWS DevOps Agent demo.
Simulates a realistic production bug where update_item is used on new orders.
This causes ConditionalCheckFailedException for every order.
"""
import json
import os
from datetime import datetime
import boto3
from botocore.exceptions import ClientError


def get_cors_headers(event):
    """
    Return CORS headers with exact origin match (no wildcards).
    
    Args:
        event: Lambda event containing headers with origin
        
    Returns:
        dict: CORS headers if origin is allowed, otherwise basic headers
    """
    # Parse allowed origins from environment variable
    allowed_origins_str = os.environ.get('ALLOWED_ORIGINS', '')
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',') if origin.strip()]
    
    # Get origin from request headers (case-insensitive)
    headers = event.get('headers', {})
    origin = headers.get('origin') or headers.get('Origin', '')
    
    # Check if origin is in allowed list
    if origin in allowed_origins:
        return {
            'Access-Control-Allow-Origin': origin,  # Exact origin, not *
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Content-Type': 'application/json'
        }
    else:
        # No CORS headers for unauthorized origins
        return {
            'Content-Type': 'application/json'
        }


def handler(event, context):
    """
    Process customer order by storing it in DynamoDB.
    
    BUG: Uses update_item with attribute_exists condition on new orders.
    This fails with ConditionalCheckFailedException because each order
    gets a unique ID that doesn't exist yet.
    
    Args:
        event: Order data (any valid JSON)
        context: Lambda runtime context (provides unique aws_request_id)
        
    Returns:
        dict: Success response with order ID
        
    Raises:
        ClientError: ConditionalCheckFailedException when order doesn't exist
    """
    # Validate event structure
    if not isinstance(event, dict):
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid request format'})
        }

    # Get appropriate CORS headers for this request
    cors_headers = get_cors_headers(event)
    
    # Generate unique order ID from AWS request ID
    order_id = context.aws_request_id
    timestamp = datetime.utcnow().isoformat()
    
    # Log order processing start
    print(f"[{timestamp}] Processing customer order")
    print(f"[{timestamp}] Order ID: {order_id}")
    print(f"[{timestamp}] Order data: {json.dumps(event)}")
    
    # Get DynamoDB table name from environment
    table_name = os.environ.get('TABLE_NAME', 'demo-user-data')
    print(f"[{timestamp}] Using DynamoDB table: {table_name}")
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    try:
        # BUG: Using update_item on a NEW order that doesn't exist yet
        # This will ALWAYS fail with ConditionalCheckFailedException
        # Should use put_item() instead for new orders
        response = table.update_item(
            Key={'id': order_id},
            UpdateExpression='SET order_data = :data, #status = :status, processed_at = :timestamp',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':data': json.dumps(event),
                ':status': 'processed',
                ':timestamp': timestamp
            },
            ConditionExpression='attribute_exists(id)',  # This condition ALWAYS fails for new orders!
            ReturnValues='ALL_NEW'
        )
        
        print(f"[{timestamp}] ✓ Order processed successfully")
        print(f"[{timestamp}] Response: {json.dumps(response, default=str)}")
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'message': 'Order processed successfully',
                'orderId': order_id,
                'timestamp': timestamp
            })
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        # Log comprehensive error details for troubleshooting
        print(f"[{timestamp}] ✗ Order processing failed")
        print(f"[{timestamp}] Error code: {error_code}")
        print(f"[{timestamp}] Error message: {error_message}")
        print(f"[{timestamp}] Order ID: {order_id}")
        print(f"[{timestamp}] Table: {table_name}")
        
        # Re-raise to mark Lambda as failed and trigger CloudWatch Alarm
        raise
