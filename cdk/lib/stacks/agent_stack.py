# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Security Responsibilities:
# - AWS manages: AWS DevOps Agent service infrastructure, AIOpsAssistantPolicy content, service availability
# - Customer manages: IAM role trust policies, role assignment, account association config, operator access
# See SECURITY.md for full shared responsibility model and threat analysis.
"""
AWS DevOps Agent Infrastructure Stack
Defines infrastructure for AWS DevOps Agent Space and monitoring
"""
from aws_cdk import CfnOutput, aws_iam as iam
from aws_cdk.aws_devopsagent import CfnAgentSpace, CfnAssociation
from constructs import Construct
from ..common.constructs.stack import Stack


class AgentStack(Stack):
    """
    CDK stack for AWS DevOps Agent infrastructure.
    
    Creates:
    - Agent Space for AI-powered incident analysis
    - IAM Service Role with monitoring permissions
    - Account Association to authorize agent access
    
    This stack provisions the AWS DevOps Agent Space and associated resources
    to enable automated monitoring and diagnosis of the demo application.
    The Agent Space monitors the demo Lambda function, CloudWatch alarm, and
    DynamoDB table to detect and diagnose the intentional bug in the order
    processing application.
    
    Regional Constraint:
    - Must be deployed to us-east-1 region (AWS DevOps Agent service availability)
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        Initialize the DevOps Agent Stack.
        
        Args:
            scope: The scope in which this stack is defined
            construct_id: The scoped construct ID
            **kwargs: Additional stack properties (env, tags, etc.)
            
        Raises:
            ValueError: If the stack is deployed to a region other than us-east-1
        """
        super().__init__(scope, construct_id, **kwargs)
        
        # Enforce regional constraint - AWS DevOps Agent service only available in us-east-1
        if self.region != "us-east-1":
            raise ValueError(
                f"DevOpsAgentStack must be deployed to us-east-1 region. "
                f"Current region: {self.region}"
            )
        
        # Create resources in proper order:
        # 1. Service Role - IAM role that the Agent Space will assume
        self.service_role = self._create_service_role()
        
        # 2. Operator App Role - IAM role for users to access the Agent console
        self.operator_role = self._create_operator_role()
        
        # 3. Agent Space - The AI agent that monitors resources
        self.agent_space = self._create_agent_space()
        
        # 4. Account Association - Authorizes Agent Space to access this account
        self.account_association = self._create_account_association()
        
        # 5. Stack Outputs - CloudFormation outputs for resource identifiers
        self._add_stack_outputs()

    def _create_service_role(self) -> iam.Role:
        """
        Create IAM Service Role for AWS DevOps Agent Space.

        The Service Role grants the Agent Space permissions to monitor and analyze
        demo application resources. It uses the AWS managed AIOpsAssistantPolicy
        which provides comprehensive read-only access to AWS services needed for
        incident investigation and diagnosis.

        Returns:
            iam.Role: The created IAM role that the Agent Space will assume
        """
        # Create the IAM role with trust policy for AWS DevOps Agent service
        service_role = iam.Role(
            self,
            "DevOpsAgentServiceRole",
            role_name="DevOpsAgentServiceRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal(
                    "aidevops.amazonaws.com",
                    conditions={
                        "StringEquals": {
                            "aws:SourceAccount": self.account
                        },
                        "ArnLike": {
                            "aws:SourceArn": f"arn:aws:aidevops:{self.region}:{self.account}:agentspace/*"
                        }
                    }
                )
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AIOpsAssistantPolicy")
            ],
            description="Service role for AWS DevOps Agent to monitor demo application resources",
        )

        return service_role

    def _create_operator_role(self) -> iam.Role:
        """
        Create IAM Operator Role for users to access the DevOps Agent console.
        
        The Operator Role allows IAM users to access the DevOps Agent Operator Web App
        and perform actions like viewing incidents, creating tasks, and invoking the agent.
        
        Returns:
            iam.Role: The created IAM role for operator access
        """
        # Create the IAM role with trust policy for AWS DevOps Agent service
        operator_role = iam.Role(
            self,
            "DevOpsAgentOperatorRole",
            role_name="DevOpsAgentRole-WebappAdmin",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal(
                    "aidevops.amazonaws.com",
                    conditions={
                        "StringEquals": {
                            "aws:SourceAccount": self.account
                        },
                        "ArnLike": {
                            "aws:SourceArn": f"arn:aws:aidevops:{self.region}:{self.account}:agentspace/*"
                        }
                    }
                )
            ),
            description="Operator role for users to access AWS DevOps Agent console",
        )
        
        # Add operator permissions for the Agent Space
        operator_role.add_to_policy(
            iam.PolicyStatement(
                sid="AllowBasicOperatorActions",
                effect=iam.Effect.ALLOW,
                actions=[
                    "aidevops:GetAgentSpace",
                    "aidevops:GetAssociation",
                    "aidevops:ListAssociations",
                    "aidevops:CreateBacklogTask",
                    "aidevops:GetBacklogTask",
                    "aidevops:UpdateBacklogTask",
                    "aidevops:ListBacklogTasks",
                    "aidevops:ListChildExecutions",
                    "aidevops:ListJournalRecords",
                    "aidevops:DiscoverTopology",
                    "aidevops:InvokeAgent",
                    "aidevops:ListGoals",
                    "aidevops:ListRecommendations",
                    "aidevops:ListExecutions",
                    "aidevops:GetRecommendation",
                    "aidevops:UpdateRecommendation",
                    "aidevops:CreateKnowledgeItem",
                    "aidevops:ListKnowledgeItems",
                    "aidevops:GetKnowledgeItem",
                    "aidevops:UpdateKnowledgeItem",
                    "aidevops:ListPendingMessages",
                    "aidevops:InitiateChatForCase",
                    "aidevops:EndChatForCase",
                    "aidevops:DescribeSupportLevel",
                    "aidevops:SendChatMessage",
                ],
                resources=[
                    f"arn:aws:aidevops:{self.region}:{self.account}:agentspace/*"
                ],
            )
        )
        
        # Add support permissions
        # SECURITY NOTE: Resource wildcard is required here — AWS Support API actions do
        # not support resource-level permissions per the AWS service authorization reference.
        # Access is constrained to us-east-1 via the aws:RequestedRegion condition below.
        # https://docs.aws.amazon.com/service-authorization/latest/reference/list_awssupport.html
        operator_role.add_to_policy(
            iam.PolicyStatement(
                sid="AllowSupportOperatorActions",
                effect=iam.Effect.ALLOW,
                actions=[
                    "support:DescribeCases",
                    "support:InitiateChatForCase",
                    "support:DescribeSupportLevel",
                ],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "aws:RequestedRegion": "us-east-1"
                    }
                },
            )
        )
        
        return operator_role

    def _create_agent_space(self) -> CfnAgentSpace:
        """
        Create AWS DevOps Agent Space for monitoring the demo application.
        
        The Agent Space is an AI-powered agent that monitors the demo application
        resources and provides automated incident analysis and diagnosis. It is
        configured to monitor:
        - Lambda function: demo-incident-lambda
        - CloudWatch alarm: demo-lambda-errors
        - DynamoDB table: demo-user-data
        
        Note: The monitoring configuration is established through the Account Association
        and the Service Role permissions, which grant access to the specific demo resources.
        
        Returns:
            CfnAgentSpace: The created Agent Space resource
        """
        # Create the Agent Space
        # Note: CfnAgentSpace only accepts 'name' and 'description' properties
        # Monitoring is configured through the Service Role permissions and Account Association
        agent_space = CfnAgentSpace(
            self,
            "DevOpsAgentSpace",
            name="DevOps Agent Demo Space",
            description="AI agent for monitoring and diagnosing the demo order processing application",
        )
        
        return agent_space

    def _create_account_association(self) -> CfnAssociation:
        """
        Create Account Association to authorize Agent Space access to AWS account.
        
        The Account Association is a bridge resource that authorizes the Agent Space
        to access and monitor resources within this AWS account. It specifies:
        - Which Agent Space is authorized (via agent_space_id)
        - Which AWS account it can access (via Configuration.Aws.AccountId)
        - Which IAM role the agent should assume (via Configuration.Aws.AssumableRoleArn)
        
        Without this association, the Agent Space exists but cannot see or interact
        with resources in the AWS account.
        
        Returns:
            CfnAssociation: The created Account Association resource
        """
        # Create the Account Association with AWS configuration
        account_association = CfnAssociation(
            self,
            "DevOpsAgentAccountAssociation",
            agent_space_id=self.agent_space.attr_agent_space_id,
            service_id="aws",
            configuration=CfnAssociation.ServiceConfigurationProperty(
                aws=CfnAssociation.AWSConfigurationProperty(
                    account_id=self.account,
                    account_type="monitor",
                    assumable_role_arn=self.service_role.role_arn,
                )
            ),
        )
        
        return account_association

    def _add_stack_outputs(self) -> None:
        """
        Add CloudFormation outputs for key resources.
        
        Creates outputs for:
        - Agent Space ID: Unique identifier for the Agent Space
        - Service Role ARN: ARN of the IAM role used by the Agent Space
        - Account Association ID: Unique identifier for the account association
        - Agent Console URL: Direct link to the Agent Space in AWS console
        
        These outputs provide easy access to resource identifiers and enable
        verification that the infrastructure was created correctly.
        """
        # Output the Agent Space ID
        CfnOutput(
            self,
            "AgentSpaceId",
            value=self.agent_space.attr_agent_space_id,
            description="The unique identifier of the AWS DevOps Agent Space",
            export_name=f"{self.stack_name}-AgentSpaceId",
        )
        
        # Output the Service Role ARN
        CfnOutput(
            self,
            "ServiceRoleArn",
            value=self.service_role.role_arn,
            description="The ARN of the IAM role used by the Agent Space to access AWS resources",
            export_name=f"{self.stack_name}-ServiceRoleArn",
        )
        
        # Output the Operator Role ARN
        CfnOutput(
            self,
            "OperatorRoleArn",
            value=self.operator_role.role_arn,
            description="The ARN of the IAM role for users to access the DevOps Agent console",
            export_name=f"{self.stack_name}-OperatorRoleArn",
        )
        
        # Output the Account Association ID
        CfnOutput(
            self,
            "AssociationId",
            value=self.account_association.attr_association_id,
            description="The unique identifier of the Account Association that authorizes the Agent Space",
            export_name=f"{self.stack_name}-AssociationId",
        )
        
        # Output the Agent Console URL
        # The console URL format for AWS DevOps Agent is:
        # https://us-east-1.console.aws.amazon.com/aidevops/home?region=us-east-1#/agent-spaces/{agent_space_id}?view=web-app
        agent_console_url = f"https://{self.region}.console.aws.amazon.com/aidevops/home?region={self.region}#/agent-spaces/{self.agent_space.attr_agent_space_id}?view=web-app"
        CfnOutput(
            self,
            "AgentConsoleUrl",
            value=agent_console_url,
            description="Direct link to the Agent Space in the AWS DevOps Agent console",
            export_name=f"{self.stack_name}-AgentConsoleUrl",
        )
