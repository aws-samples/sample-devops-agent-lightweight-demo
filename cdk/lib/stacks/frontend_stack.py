# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Security Responsibilities:
# - AWS manages: S3 encryption infrastructure, CloudFront TLS termination, edge security, OAC enforcement
# - Customer manages: Bucket policies, Block Public Access settings, CloudFront config, runtime config security
# See SECURITY.md for full shared responsibility model and threat analysis.
"""Frontend Stack - Amazon S3 + Amazon CloudFront for React app"""
import time
import subprocess
from pathlib import Path
from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    Fn,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    custom_resources as cr,
)
from constructs import Construct


class FrontendStack(Stack):
    """Static website hosting with Amazon S3 and Amazon CloudFront"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        user_pool_id: str,
        user_pool_client_id: str,
        identity_pool_id: str,
        api_url: str,
        process_order_lambda_name: str,
        alarm_status_lambda_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Build frontend (no config injection needed - config is loaded at runtime)
        cdk_dir = Path(__file__).parent.parent.parent
        frontend_dir = cdk_dir.parent / "portal" / "frontend"
        dist_dir = frontend_dir / "dist"

        try:
            # Install dependencies if needed
            node_modules = frontend_dir / "node_modules"
            if not node_modules.exists():
                print("Installing frontend dependencies...")
                subprocess.run(
                    ["npm", "install"],
                    cwd=str(frontend_dir),
                    check=True,
                )

            # Build frontend (no env vars needed)
            print("Building frontend...")
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(frontend_dir),
                check=True,
                capture_output=True,
                text=True,
            )
            print("Frontend build completed successfully")
        except Exception as e:
            print(f"Warning: Frontend build failed: {e}")
            if not dist_dir.exists():
                print("Creating minimal placeholder dist/")
                dist_dir.mkdir(parents=True, exist_ok=True)
                (dist_dir / "index.html").write_text(
                    "<html><body><h1>Frontend not built yet. Run npm run build in portal/frontend/</h1></body></html>"
                )

        # Write a deploy marker to bust CDK's asset hash cache
        # This ensures BucketDeployment always re-uploads files to S3
        (dist_dir / ".deploy-marker").write_text(str(time.time()))

        # S3 bucket for website
        # Security: SSE-S3 encryption, Block Public Access, TLS enforcement
        # Data classification: Public content (HTML, CSS, JS) - no sensitive data
        # Key management: AWS-managed keys sufficient for static website assets
        self.website_bucket = s3.Bucket(
            self,
            "WebsiteBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # CloudFront distribution with Origin Access Control for S3
        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(self.website_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
            ],
        )

        # Deploy compiled frontend assets
        self.website_deployment = s3deploy.BucketDeployment(
            self,
            "DeployWebsite",
            sources=[s3deploy.Source.asset("../portal/frontend/dist")],
            destination_bucket=self.website_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
            prune=False,
        )

        # Deploy runtime config to S3 with auth and API settings
        runtime_config_content = Fn.join("", [
            "window.__config = {\n",
            '  userPoolId: "', user_pool_id, '",\n',
            '  userPoolClientId: "', user_pool_client_id, '",\n',
            '  identityPoolId: "', identity_pool_id, '",\n',
            '  apiUrl: "', api_url, '"\n',
            "};\n",
        ])

        put_config_call = cr.AwsSdkCall(
            service="S3",
            action="putObject",
            parameters={
                "Bucket": self.website_bucket.bucket_name,
                "Key": "runtime-config.js",
                "Body": runtime_config_content,
                "ContentType": "application/javascript",
            },
            physical_resource_id=cr.PhysicalResourceId.of("runtime-config-js"),
        )

        runtime_config_resource = cr.AwsCustomResource(
            self,
            "DeployRuntimeConfig",
            on_create=put_config_call,
            on_update=put_config_call,
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["s3:PutObject"],
                    resources=[self.website_bucket.arn_for_objects("runtime-config.js")],
                ),
            ]),
        )
        runtime_config_resource.node.add_dependency(self.website_deployment)

        # Update Cognito User Pool Client callback URLs to include CloudFront domain
        # This is done via AwsCustomResource to avoid circular dependency between
        # frontend stack (needs auth outputs) and auth stack (needs CloudFront domain)
        cloudfront_url = Fn.join("", ["https://", distribution.distribution_domain_name])

        cr.AwsCustomResource(
            self,
            "UpdateCognitoCallbackUrls",
            on_create=cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="updateUserPoolClient",
                parameters={
                    "UserPoolId": user_pool_id,
                    "ClientId": user_pool_client_id,
                    "CallbackURLs": [cloudfront_url],
                    "LogoutURLs": [cloudfront_url],
                    "AllowedOAuthFlows": ["code"],
                    "AllowedOAuthScopes": ["email", "openid", "profile"],
                    "AllowedOAuthFlowsUserPoolClient": True,
                    "SupportedIdentityProviders": ["COGNITO"],
                    "ExplicitAuthFlows": [
                        "ALLOW_USER_SRP_AUTH",
                        "ALLOW_USER_PASSWORD_AUTH",
                        "ALLOW_REFRESH_TOKEN_AUTH",
                    ],
                },
                physical_resource_id=cr.PhysicalResourceId.of("cognito-callback-urls"),
            ),
            on_update=cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="updateUserPoolClient",
                parameters={
                    "UserPoolId": user_pool_id,
                    "ClientId": user_pool_client_id,
                    "CallbackURLs": [cloudfront_url],
                    "LogoutURLs": [cloudfront_url],
                    "AllowedOAuthFlows": ["code"],
                    "AllowedOAuthScopes": ["email", "openid", "profile"],
                    "AllowedOAuthFlowsUserPoolClient": True,
                    "SupportedIdentityProviders": ["COGNITO"],
                    "ExplicitAuthFlows": [
                        "ALLOW_USER_SRP_AUTH",
                        "ALLOW_USER_PASSWORD_AUTH",
                        "ALLOW_REFRESH_TOKEN_AUTH",
                    ],
                },
                physical_resource_id=cr.PhysicalResourceId.of("cognito-callback-urls"),
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["cognito-idp:UpdateUserPoolClient", "cognito-idp:DescribeUserPoolClient"],
                    resources=[
                        Fn.join("", [
                            "arn:aws:cognito-idp:",
                            Stack.of(self).region,
                            ":",
                            Stack.of(self).account,
                            ":userpool/",
                            user_pool_id,
                        ]),
                    ],
                ),
            ]),
        )

        # Update Lambda ALLOWED_ORIGINS env vars to include CloudFront URL
        # CORS allowlist is the CloudFront origin only. The app is served from
        # CloudFront (no local dev server); the API stack bootstraps with an empty
        # allowlist and this resource sets the CloudFront origin after the
        # distribution is created (breaking the cross-stack cyclic dependency).
        allowed_origins_value = cloudfront_url

        update_process_order_origins = cr.AwsCustomResource(
            self,
            "UpdateProcessOrderLambdaOrigins",
            on_create=cr.AwsSdkCall(
                service="Lambda",
                action="updateFunctionConfiguration",
                parameters={
                    "FunctionName": process_order_lambda_name,
                    "Environment": {
                        "Variables": {
                            "ALLOWED_ORIGINS": allowed_origins_value,
                            "TABLE_NAME": "demo-user-data",
                        }
                    },
                },
                physical_resource_id=cr.PhysicalResourceId.of("update-process-order-lambda-origins"),
            ),
            on_update=cr.AwsSdkCall(
                service="Lambda",
                action="updateFunctionConfiguration",
                parameters={
                    "FunctionName": process_order_lambda_name,
                    "Environment": {
                        "Variables": {
                            "ALLOWED_ORIGINS": allowed_origins_value,
                            "TABLE_NAME": "demo-user-data",
                        }
                    },
                },
                physical_resource_id=cr.PhysicalResourceId.of("update-process-order-lambda-origins"),
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["lambda:UpdateFunctionConfiguration", "lambda:GetFunctionConfiguration"],
                    resources=[
                        Fn.join("", [
                            "arn:aws:lambda:",
                            Stack.of(self).region,
                            ":",
                            Stack.of(self).account,
                            ":function:",
                            process_order_lambda_name,
                        ]),
                    ],
                ),
            ]),
        )
        update_process_order_origins.node.add_dependency(self.website_deployment)

        update_alarm_status_origins = cr.AwsCustomResource(
            self,
            "UpdateAlarmStatusLambdaOrigins",
            on_create=cr.AwsSdkCall(
                service="Lambda",
                action="updateFunctionConfiguration",
                parameters={
                    "FunctionName": alarm_status_lambda_name,
                    "Environment": {
                        "Variables": {
                            "ALLOWED_ORIGINS": allowed_origins_value,
                        }
                    },
                },
                physical_resource_id=cr.PhysicalResourceId.of("update-alarm-status-lambda-origins"),
            ),
            on_update=cr.AwsSdkCall(
                service="Lambda",
                action="updateFunctionConfiguration",
                parameters={
                    "FunctionName": alarm_status_lambda_name,
                    "Environment": {
                        "Variables": {
                            "ALLOWED_ORIGINS": allowed_origins_value,
                        }
                    },
                },
                physical_resource_id=cr.PhysicalResourceId.of("update-alarm-status-lambda-origins"),
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["lambda:UpdateFunctionConfiguration", "lambda:GetFunctionConfiguration"],
                    resources=[
                        Fn.join("", [
                            "arn:aws:lambda:",
                            Stack.of(self).region,
                            ":",
                            Stack.of(self).account,
                            ":function:",
                            alarm_status_lambda_name,
                        ]),
                    ],
                ),
            ]),
        )
        update_alarm_status_origins.node.add_dependency(self.website_deployment)

        # Outputs
        CfnOutput(
            self,
            "CloudFrontUrl",
            value=f"https://{distribution.distribution_domain_name}",
            description="CloudFront URL for demo portal",
        )

        CfnOutput(
            self,
            "BucketName",
            value=self.website_bucket.bucket_name,
            description="S3 bucket name",
        )

        self.distribution = distribution
        self.bucket = self.website_bucket
