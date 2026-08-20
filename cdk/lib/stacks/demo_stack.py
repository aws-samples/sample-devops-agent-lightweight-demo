# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
AWS DevOps Agent Demo Stack
Defines all infrastructure resources for the demo
"""
from aws_cdk import (
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_cloudwatch as cloudwatch,
)
from constructs import Construct
from ..common.constructs.stack import Stack
import os


class DemoStack(Stack):
    """
    Main CDK stack for AWS DevOps Agent Demo
    
    Creates:
    - DynamoDB table for order storage
    - Lambda function for order processing (with intentional bug)
    - CloudWatch alarm for error detection
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ========================================
        # DynamoDB Table for Order Storage
        # ========================================
        self.orders_table = dynamodb.Table(
            self,
            "OrdersTable",
            table_name="demo-user-data",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,  # For demo purposes
            point_in_time_recovery=False,  # Not needed for demo
        )

        # ========================================
        # Lambda Function - Order Processing
        # ========================================
        # Get path to Lambda code (from cdk/lib/stacks to project root)
        lambda_code_path = os.path.join(
            os.path.dirname(__file__),  # cdk/lib/stacks
            "..", "..", "..",  # up to project root
            "src"
        )

        self.order_processing_function = lambda_.Function(
            self,
            "OrderProcessingFunction",
            function_name="demo-incident-lambda",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="lambda_function.handler",
            code=lambda_.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(10),
            memory_size=128,
            description="Order Processing Lambda for AWS DevOps Agent demo - intentionally contains bug",
            environment={
                "TABLE_NAME": self.orders_table.table_name,
            },
            retry_attempts=0,  # Don't retry failures for demo
        )

        # Grant Lambda minimum required DynamoDB permissions (least privilege)
        self.orders_table.grant(
            self.order_processing_function,
            "dynamodb:PutItem",
            "dynamodb:UpdateItem",
            "dynamodb:GetItem",
        )

        # ========================================
        # CloudWatch Alarm for Lambda Errors
        # ========================================
        # Note: No SNS topic needed - alarm is monitored by AWS DevOps Agent
        # and displayed in the demo portal UI
        self.error_alarm = cloudwatch.Alarm(
            self,
            "LambdaErrorAlarm",
            alarm_name="demo-lambda-errors",
            alarm_description="Triggers when Order Processing Lambda encounters errors",
            metric=self.order_processing_function.metric_errors(
                period=Duration.minutes(1),
                statistic="Sum",
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # ========================================
        # CloudFormation Outputs
        # ========================================
        CfnOutput(
            self,
            "LambdaFunctionName",
            value=self.order_processing_function.function_name,
            description="Order Processing Lambda Function Name",
            export_name="DevOpsDemo-LambdaName",
        )

        CfnOutput(
            self,
            "LambdaFunctionArn",
            value=self.order_processing_function.function_arn,
            description="Order Processing Lambda Function ARN",
            export_name="DevOpsDemo-LambdaArn",
        )

        CfnOutput(
            self,
            "LambdaRoleName",
            value=self.order_processing_function.role.role_name,
            description="Lambda Execution Role Name",
            export_name="DevOpsDemo-LambdaRoleName",
        )

        CfnOutput(
            self,
            "DynamoDBTableName",
            value=self.orders_table.table_name,
            description="DynamoDB Table for Orders",
            export_name="DevOpsDemo-TableName",
        )

        CfnOutput(
            self,
            "CloudWatchAlarmName",
            value=self.error_alarm.alarm_name,
            description="CloudWatch Alarm for Lambda Errors",
            export_name="DevOpsDemo-AlarmName",
        )
