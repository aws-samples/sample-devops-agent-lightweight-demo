# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
Cognito User Auto-Creation Custom Resource
Creates a demo user with random password at deployment time
"""
import secrets
import string

from aws_cdk import (
    custom_resources as cr,
    aws_iam as iam,
    aws_cognito as cognito,
    SecretValue,
)
from constructs import Construct


def _generate_password(length: int = 16) -> str:
    """Generate a random password meeting Cognito policy requirements.

    Guarantees at least one uppercase, one lowercase, one digit, and one symbol,
    then fills the remaining characters from the full alphabet and shuffles.
    """
    symbols = "!@#$%^&*()-_=+"
    alphabet = string.ascii_letters + string.digits + symbols

    # Guarantee one character from each required class
    required = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(symbols),
    ]
    remaining = [secrets.choice(alphabet) for _ in range(length - len(required))]
    password_chars = required + remaining
    # Shuffle so the required chars aren't always at the front
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


class CognitoAutoUser(Construct):
    """
    Creates a Cognito user automatically at deployment with a random password
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        user_pool: cognito.IUserPool,
        username: str = "demo@example.com",
    ):
        super().__init__(scope, id)

        self.username = username

        # Custom resource to create user
        create_user = cr.AwsCustomResource(
            self,
            "CreateUser",
            on_create=cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="adminCreateUser",
                parameters={
                    "UserPoolId": user_pool.user_pool_id,
                    "Username": username,
                    "MessageAction": "SUPPRESS",  # Don't send email
                    "UserAttributes": [
                        {"Name": "email", "Value": username},
                        {"Name": "email_verified", "Value": "true"},
                    ],
                },
                physical_resource_id=cr.PhysicalResourceId.of(f"demo-user-{username}"),
            ),
            on_delete=cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="adminDeleteUser",
                parameters={
                    "UserPoolId": user_pool.user_pool_id,
                    "Username": username,
                },
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "cognito-idp:AdminCreateUser",
                            "cognito-idp:AdminDeleteUser",
                            "cognito-idp:AdminSetUserPassword",
                        ],
                        resources=[user_pool.user_pool_arn],
                    )
                ]
            ),
        )

        # Generate random password at synth time (16 chars, meets Cognito policy)
        password = SecretValue.unsafe_plain_text(_generate_password(16))

        # Set permanent password
        # Note: physical_resource_id includes the password hash to force re-execution
        # when the password changes (e.g., on redeploy after stack destruction)
        import hashlib
        password_hash = hashlib.sha256(password.unsafe_unwrap().encode()).hexdigest()[:8]
        set_password = cr.AwsCustomResource(
            self,
            "SetPassword",
            on_create=cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="adminSetUserPassword",
                parameters={
                    "UserPoolId": user_pool.user_pool_id,
                    "Username": username,
                    "Password": password.unsafe_unwrap(),
                    "Permanent": True,
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"demo-user-password-{username}-{password_hash}"
                ),
            ),
            on_update=cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="adminSetUserPassword",
                parameters={
                    "UserPoolId": user_pool.user_pool_id,
                    "Username": username,
                    "Password": password.unsafe_unwrap(),
                    "Permanent": True,
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"demo-user-password-{username}-{password_hash}"
                ),
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["cognito-idp:AdminSetUserPassword"],
                        resources=[user_pool.user_pool_arn],
                    )
                ]
            ),
        )

        # Ensure password is set after user is created
        set_password.node.add_dependency(create_user)

        # Store password so auth_stack can expose it via CfnOutput
        self.password = password
