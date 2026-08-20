#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
AWS DevOps Agent Demo - CDK Application
Infrastructure-as-Code deployment using AWS CDK for Python
"""
import os
import json
import aws_cdk as cdk
from lib.stage import ApplicationStage

app = cdk.App()

# Read cdk.json for configuration
cdk_json_path = os.path.join(os.path.dirname(__file__), "cdk.json")
with open(cdk_json_path) as f:
    cdk_config = json.load(f)

# Get configuration
project_id = cdk_config.get("projectId", "devops-agent")
stage_name = cdk_config.get("stage", "dev")
accounts = cdk_config.get("accounts", {})
account_config = accounts.get(stage_name, {})

# Environment configuration
env = cdk.Environment(
    account=account_config.get("id") or os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=account_config.get("region", "us-east-1"),
)

# Create application stage
ApplicationStage(
    app,
    stage_name,
    env=env,
)

app.synth()
