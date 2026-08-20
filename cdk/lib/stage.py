# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
Application Stage - Wraps all stacks for proper context handling
"""
from aws_cdk import Stage, Tags, Aspects
from constructs import Construct
from cdk_nag import NagSuppressions, AwsSolutionsChecks
from .stacks.auth_stack import AuthStack
from .stacks.demo_stack import DemoStack
from .stacks.agent_stack import AgentStack
from .stacks.api_stack import ApiStack
from .stacks.frontend_stack import FrontendStack


class ApplicationStage(Stage):
    """
    Application stage containing all demo stacks
    """

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Get project configuration
        project_id = self.node.try_get_context("projectId") or "devops-agent"
        
        # Tag all resources with project ID
        Tags.of(self).add("projectId", project_id)

        # Demo Stack (independent - creates Lambda and DynamoDB)
        self.demo = DemoStack(
            self,
            "demo",
            description="AWS DevOps Agent Demo - Order Processing Simulation",
        )

        # Auth Stack (created before API so outputs are available)
        # Auth Stack (created before API so outputs are available)
        # NOTE: callback_urls below is a transient creation-time placeholder required
        # by Cognito's OAuth code flow. The frontend stack overwrites the live
        # callback/logout URLs with the CloudFront origin only (no localhost / local dev).
        self.auth = AuthStack(
            self,
            "auth",
            description="Authentication with Cognito and Identity Pool",
            callback_urls=[
                "https://example.com/callback",
            ],
        )

        # API Stack (created BEFORE Frontend)
        # allowed_origins starts empty; the frontend stack sets the CloudFront origin
        # on the Lambdas after the distribution exists (breaks the cyclic dependency).
        self.api = ApiStack(
            self,
            "api",
            user_pool=self.auth.user_pool,
            process_order_lambda=self.demo.order_processing_function,
            alarm_name=self.demo.error_alarm.alarm_name,
            allowed_origins=[],
            description="API Gateway for Demo Portal",
        )

        # Frontend Stack (created AFTER API - receives api_url directly)
        self.frontend = FrontendStack(
            self,
            "frontend",
            user_pool_id=self.auth.user_pool.user_pool_id,
            user_pool_client_id=self.auth.user_pool_client.user_pool_client_id,
            identity_pool_id=self.auth.identity_pool.ref,
            api_url=self.api.api_url,
            process_order_lambda_name=self.demo.order_processing_function.function_name,
            alarm_status_lambda_name=self.api.alarm_status_lambda.function_name,
            description="Frontend - S3 + CloudFront",
        )

        # Agent Stack
        self.agent = AgentStack(
            self,
            "agent",
            description="AWS DevOps Agent Infrastructure - AI-powered monitoring and diagnosis",
        )

        # Add CDK Nag suppressions
        NagSuppressions.add_resource_suppressions(
            self,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "Managed policies: Lambda basic execution role, and the AWS-managed AIOpsAssistantPolicy which is required by AWS DevOps Agent for read-only monitoring.",
                    "appliesTo": [
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/AIOpsAssistantPolicy",
                    ],
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "High-level constructs can require wildcards for dynamic resource creation.",
                },
                {
                    "id": "AwsSolutions-L1",
                    "reason": "High-level constructs can set their own runtimes.",
                },
                {
                    "id": "AwsSolutions-COG2",
                    "reason": "MFA not required for demo purposes.",
                },
                {
                    "id": "AwsSolutions-COG3",
                    "reason": "Advanced security mode not required for demo purposes.",
                },
                {
                    "id": "AwsSolutions-COG8",
                    "reason": "Cognito plus/feature tier is not required for a short-lived demo user pool.",
                },
                {
                    "id": "AwsSolutions-S1",
                    "reason": "The website bucket serves only public static assets; CloudFront and API Gateway access logs provide the audit trail. S3 server access logs are not needed for the demo.",
                },
                {
                    "id": "AwsSolutions-CFR3",
                    "reason": "CloudFront access logging is not enabled for this short-lived demo; API Gateway access logs cover the request audit trail.",
                },
                {
                    "id": "AwsSolutions-CFR1",
                    "reason": "Geo restrictions are not required for a globally-accessible demo.",
                },
                {
                    "id": "AwsSolutions-CFR2",
                    "reason": "CloudFront WAF integration is not required for a short-lived demo; API throttling and the Cognito user-pool WAF are in place.",
                },
                {
                    "id": "AwsSolutions-APIG3",
                    "reason": "API-stage WAF is not required for the demo; throttling is enabled and the Cognito user pool is WAF-protected.",
                },
                {
                    "id": "AwsSolutions-DDB3",
                    "reason": "Point-in-time recovery is not required for ephemeral demo order data (accepted risk).",
                },
                {
                    "id": "AwsSolutions-CFR4",
                    "reason": "The distribution uses the default CloudFront certificate (*.cloudfront.net), for which a minimum TLS version cannot be enforced; a custom domain + ACM certificate is out of scope for this demo. minimum_protocol_version is set so the policy applies if a custom certificate is ever added.",
                },
            ],
            apply_to_children=True,
        )
        
        # Apply CDK Nag checks (AWS Solutions ruleset)
        Aspects.of(self).add(AwsSolutionsChecks())
