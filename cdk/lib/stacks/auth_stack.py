# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Security Responsibilities:
# - AWS manages: Cognito infrastructure security, encryption at rest, service availability
# - Customer manages: Password policies, MFA configuration, WAF rules, IAM permissions
# See SECURITY.md for full shared responsibility model and threat analysis.
"""
Authentication Stack with Amazon Cognito User Pool, Identity Pool, and AWS WAF
"""
from aws_cdk import (
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_cognito as cognito,
    aws_wafv2 as wafv2,
    aws_iam as iam,
)
from constructs import Construct
from ..common.constructs.stack import Stack
from ..common.constructs.cognito_user import CognitoAutoUser
from ..common.utilities import create_waf_managed_rules


class AuthStack(Stack):
    """
    Authentication stack providing:
    - Amazon Cognito User Pool with email sign-in
    - User Pool Groups (Admin, Users)
    - Identity Pool for AWS resource access
    - AWS WAF protection with rate limiting and managed rules
    """

    def __init__(
        self, scope: Construct, id: str, callback_urls: list[str] = None, **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        # Default callback URLs — transient HTTPS placeholder for the Cognito OAuth
        # code flow at creation time. The frontend stack overwrites this with the
        # live CloudFront origin (no localhost / local dev).
        if callback_urls is None:
            callback_urls = ["https://example.com/callback"]

        # Cognito User Pool
        # CRITICAL: self_sign_up_enabled=False for demo security compliance (admin-only user creation)
        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True)
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # User Pool Groups
        cognito.CfnUserPoolGroup(
            self,
            "AdminGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="Admin",
            description="Administrator users with full access",
        )

        cognito.CfnUserPoolGroup(
            self,
            "UsersGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="Users",
            description="Standard users with limited access",
        )

        # User Pool Client
        token_validity = Duration.hours(8)
        self.user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=self.user_pool,
            auth_flows=cognito.AuthFlow(user_srp=True, user_password=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=callback_urls,
                logout_urls=callback_urls,
            ),
            access_token_validity=token_validity,
            id_token_validity=token_validity,
            refresh_token_validity=token_validity,
        )

        # Identity Pool
        self.identity_pool = cognito.CfnIdentityPool(
            self,
            "IdentityPool",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.user_pool_client.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name,
                )
            ],
        )

        # Identity Pool Roles
        authenticated_role = iam.Role(
            self,
            "AuthenticatedRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
        )

        # Deny all for unauthenticated (defense in depth)
        unauthenticated_role = iam.Role(
            self,
            "UnauthenticatedRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "unauthenticated"
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
        )
        unauthenticated_role.add_to_policy(
            # Defense in depth: explicitly deny all actions on all resources for
            # unauthenticated identities. allow_unauthenticated_identities=False already
            # enforces this at the identity pool level; this blanket DENY is an intentional
            # second layer. The "*"/"*" pattern is required to deny everything.
            iam.PolicyStatement(effect=iam.Effect.DENY, actions=["*"], resources=["*"])
        )

        # Attach roles to identity pool
        cognito.CfnIdentityPoolRoleAttachment(
            self,
            "IdentityPoolRoleAttachment",
            identity_pool_id=self.identity_pool.ref,
            roles={
                "authenticated": authenticated_role.role_arn,
                "unauthenticated": unauthenticated_role.role_arn,
            },
        )

        # AWS WAF for User Pool
        self.web_acl = wafv2.CfnWebACL(
            self,
            "UserPoolWebACL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope="REGIONAL",
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="UserPoolWebACL",
                sampled_requests_enabled=True,
            ),
            rules=[
                # Rate limiting rule
                wafv2.CfnWebACL.RuleProperty(
                    name="RateLimitRule",
                    priority=0,
                    statement=wafv2.CfnWebACL.StatementProperty(
                        rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                            limit=3000, aggregate_key_type="IP"
                        )
                    ),
                    action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="RateLimitRule",
                        sampled_requests_enabled=True,
                    ),
                ),
                # AWS Managed Rules
                *create_waf_managed_rules(
                    "regional",
                    1,
                    [
                        {"name": "AWSManagedRulesCommonRuleSet"},
                        {"name": "AWSManagedRulesKnownBadInputsRuleSet"},
                        {"name": "AWSManagedRulesSQLiRuleSet"},
                    ],
                ),
            ],
        )

        # Associate AWS WAF with User Pool
        wafv2.CfnWebACLAssociation(
            self,
            "UserPoolWebACLAssociation",
            resource_arn=self.user_pool.user_pool_arn,
            web_acl_arn=self.web_acl.attr_arn,
        )

        # Auto-create demo user
        demo_user = CognitoAutoUser(
            self,
            "DemoUser",
            user_pool=self.user_pool,
            username="demo@example.com",
        )

        # Output demo credentials
        CfnOutput(
            self,
            "DemoUsername",
            value="demo@example.com",
            description="Demo user login username",
        )

        # DEMO ONLY: Password exposure in CloudFormation outputs is ONLY acceptable for
        # short-lived, isolated demo accounts that are torn down after use.
        # PRODUCTION: Store credentials in AWS Secrets Manager and retrieve them
        # programmatically. NEVER expose credentials in CloudFormation outputs.
        # See: https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html
        CfnOutput(
            self,
            "DemoPassword",
            value=demo_user.password.unsafe_unwrap(),
            description="Demo user login password (auto-generated)",
        )

        # Outputs
        CfnOutput(
            self,
            "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID",
        )

        CfnOutput(
            self,
            "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID",
        )

        CfnOutput(
            self,
            "IdentityPoolId",
            value=self.identity_pool.ref,
            description="Cognito Identity Pool ID",
        )

        CfnOutput(
            self,
            "AuthenticatedRoleArn",
            value=authenticated_role.role_arn,
            description="IAM Role for authenticated users",
        )
