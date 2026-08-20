# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Security Responsibilities:
# - AWS manages: API Gateway infrastructure, TLS termination, DDoS protection, Cognito JWT verification
# - Customer manages: Authorizer configuration, CORS policies, throttling limits, request validation
# See SECURITY.md for full shared responsibility model and threat analysis.
"""Amazon API Gateway Stack for Demo Portal"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_apigateway as apigw,
    aws_lambda as lambda_,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_logs as logs,
    CfnOutput,
)
from constructs import Construct


class ApiStack(Stack):
    """Amazon API Gateway with Amazon Cognito authorizer for demo portal"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        user_pool: cognito.UserPool,
        process_order_lambda: lambda_.Function,
        alarm_name: str,
        allowed_origins: list[str],
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda for alarm status
        self.alarm_status_lambda = lambda_.Function(
            self,
            "AlarmStatusFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=lambda_.Code.from_inline(
                f"""
import json
import os
import boto3

cloudwatch = boto3.client('cloudwatch')
ALARM_NAME = '{alarm_name}'

def get_cors_headers(event):
    \"\"\"
    Return CORS headers with exact origin match (no wildcards).
    
    Args:
        event: Lambda event containing headers with origin
        
    Returns:
        dict: CORS headers if origin is allowed, otherwise basic headers
    \"\"\"
    # Parse allowed origins from environment variable
    allowed_origins_str = os.environ.get('ALLOWED_ORIGINS', '')
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',') if origin.strip()]
    
    # Get origin from request headers (case-insensitive)
    headers = event.get('headers', {{}})
    origin = headers.get('origin') or headers.get('Origin', '')
    
    # Check if origin is in allowed list
    if origin in allowed_origins:
        return {{
            'Access-Control-Allow-Origin': origin,  # Exact origin, not *
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Content-Type': 'application/json'
        }}
    else:
        # No CORS headers for unauthorized origins
        return {{
            'Content-Type': 'application/json'
        }}

def handler(event, context):
    # Validate event structure
    if not isinstance(event, dict):
        return {{
            'statusCode': 400,
            'headers': {{'Content-Type': 'application/json'}},
            'body': json.dumps({{'error': 'Invalid request format'}})
        }}

    # Get appropriate CORS headers for this request
    cors_headers = get_cors_headers(event)
    
    try:
        response = cloudwatch.describe_alarms(AlarmNames=[ALARM_NAME])
        
        if not response['MetricAlarms']:
            return {{
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({{'exists': False}})
            }}
        
        alarm = response['MetricAlarms'][0]
        
        return {{
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({{
                'exists': True,
                'state': alarm['StateValue'],
                'reason': alarm.get('StateReason', ''),
                'updatedAt': alarm['StateUpdatedTimestamp'].isoformat(),
                'alarmName': alarm['AlarmName'],
                'alarmDescription': alarm.get('AlarmDescription', ''),
                'metricName': alarm['MetricName'],
                'namespace': alarm['Namespace'],
                'threshold': alarm['Threshold'],
                'comparisonOperator': alarm['ComparisonOperator'],
                'period': alarm['Period']
            }})
        }}
    except Exception as e:
        return {{
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({{'error': str(e)}})
        }}
"""
            ),
        )

        # Grant CloudWatch permissions (scoped to specific alarm)
        self.alarm_status_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:DescribeAlarms"],
                resources=[
                    f"arn:aws:cloudwatch:{Stack.of(self).region}:{Stack.of(self).account}:alarm:{alarm_name}"
                ],
            )
        )

        # Add ALLOWED_ORIGINS environment variable to Lambda functions
        process_order_lambda.add_environment(
            "ALLOWED_ORIGINS",
            ",".join(allowed_origins)
        )
        
        self.alarm_status_lambda.add_environment(
            "ALLOWED_ORIGINS",
            ",".join(allowed_origins)
        )

        # CloudWatch Log Group for API access + execution logs
        log_group = logs.LogGroup(
            self,
            "ApiLogGroup",
            log_group_name="/aws/apigateway/demo-portal-api",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create API Gateway with CORS, throttling, and logging
        # Preflight uses ALL_ORIGINS (no credentials) to avoid cyclic dependency
        # with CloudFront URL. Lambda responses handle per-origin CORS with credentials.
        api = apigw.RestApi(
            self,
            "DemoApi",
            rest_api_name="demo-portal-api",
            description="API for AWS DevOps Agent Demo Portal",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"],
            ),
            deploy_options=apigw.StageOptions(
                access_log_destination=apigw.LogGroupLogDestination(log_group),
                access_log_format=apigw.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True,
                ),
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
                throttling_rate_limit=10,  # requests per second
                throttling_burst_limit=20,  # burst capacity
            ),
        )

        # Add CORS headers to API Gateway error responses (4xx and 5xx).
        # Uses wildcard '*' because these responses are generated by API Gateway
        # itself (e.g., Cognito auth failure, throttling, malformed request) —
        # the Lambda never executes, so it can't set per-origin CORS headers.
        # Without these, the browser blocks the error response entirely and the
        # frontend can't display meaningful error messages.
        # The wildcard is acceptable here: these responses only contain generic
        # error codes (401, 403, 429, 500), not sensitive application data.
        # Actual request CORS is enforced by Lambda via exact-origin matching.
        api.add_gateway_response(
            "Default4xx",
            type=apigw.ResponseType.DEFAULT_4_XX,
            response_headers={
                "Access-Control-Allow-Origin": "'*'",
                "Access-Control-Allow-Headers": "'Content-Type,Authorization'",
                "Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS'",
            },
        )

        api.add_gateway_response(
            "Default5xx",
            type=apigw.ResponseType.DEFAULT_5_XX,
            response_headers={
                "Access-Control-Allow-Origin": "'*'",
                "Access-Control-Allow-Headers": "'Content-Type,Authorization'",
                "Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS'",
            },
        )

        # Request Validator
        request_validator = apigw.RequestValidator(
            self,
            "RequestValidator",
            rest_api=api,
            validate_request_body=True,
            validate_request_parameters=True,
        )

        # Cognito authorizer
        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            "CognitoAuthorizer",
            cognito_user_pools=[user_pool],
        )

        # Process order endpoint
        process_order = api.root.add_resource("process-order")
        process_order.add_method(
            "POST",
            apigw.LambdaIntegration(process_order_lambda),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )

        # Alarm status endpoint
        alarm_status = api.root.add_resource("alarm-status")
        alarm_status.add_method(
            "GET",
            apigw.LambdaIntegration(self.alarm_status_lambda),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )

        # Output API URL
        CfnOutput(
            self,
            "ApiUrl",
            value=api.url,
            description="API Gateway URL",
        )

        self.api = api
        self.api_url = api.url
