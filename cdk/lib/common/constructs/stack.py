# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
Base Stack class with automatic tagging
"""
from aws_cdk import Stack as CdkStack, Tags
from constructs import Construct


class Stack(CdkStack):
    """
    Extended Stack with automatic project tagging
    """

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Auto-tag all resources
        project_id = self.node.try_get_context("projectId") or "devops-agent"
        Tags.of(self).add("Project", project_id)
        Tags.of(self).add("ManagedBy", "CDK")
