#!/bin/bash

# Stack names match CDK stage prefix from cdk.json
STAGE="dev"
DEMO_STACK_NAME="${STAGE}-demo"
AUTH_STACK_NAME="${STAGE}-auth"
API_STACK_NAME="${STAGE}-api"
FRONTEND_STACK_NAME="${STAGE}-frontend"
AGENT_STACK_NAME="${STAGE}-agent"

LOG_GROUP_NAME="/aws/lambda/demo-incident-lambda"

echo "========================================="
echo "AWS DevOps Agent Demo - Verification"
echo "========================================="
echo ""

ERRORS=0

# Helper: fetch stack outputs as JSON
get_stack_outputs() {
  aws cloudformation describe-stacks --stack-name "$1" --query 'Stacks[0].Outputs' --output json 2>/dev/null
}

# Helper: extract an output value by key
get_output_value() {
  echo "$1" | grep -A 2 "\"OutputKey\": \"$2\"" | grep '"OutputValue"' | cut -d'"' -f4
}

# =========================================
# 1. Demo Stack
# =========================================
echo "--- Demo Stack ($DEMO_STACK_NAME) ---"
DEMO_OUTPUTS=$(get_stack_outputs "$DEMO_STACK_NAME")

if [ $? -ne 0 ] || [ -z "$DEMO_OUTPUTS" ] || [ "$DEMO_OUTPUTS" = "null" ]; then
  echo "❌ Stack not found: $DEMO_STACK_NAME"
  echo "   Run 'npm run setup' to deploy first"
  ERRORS=$((ERRORS + 1))
else
  echo "✅ Stack found: $DEMO_STACK_NAME"

  FUNCTION_NAME=$(get_output_value "$DEMO_OUTPUTS" "LambdaFunctionName")
  ROLE_NAME=$(get_output_value "$DEMO_OUTPUTS" "LambdaRoleName")
  ALARM_NAME=$(get_output_value "$DEMO_OUTPUTS" "CloudWatchAlarmName")

  # Lambda function exists
  if [ -n "$FUNCTION_NAME" ]; then
    if aws lambda get-function --function-name "$FUNCTION_NAME" > /dev/null 2>&1; then
      echo "✅ Lambda function exists: $FUNCTION_NAME"
    else
      echo "❌ Lambda function not found: $FUNCTION_NAME"
      ERRORS=$((ERRORS + 1))
    fi
  else
    echo "❌ LambdaFunctionName output missing"
    ERRORS=$((ERRORS + 1))
  fi

  # IAM role exists
  if [ -n "$ROLE_NAME" ]; then
    if aws iam get-role --role-name "$ROLE_NAME" > /dev/null 2>&1; then
      echo "✅ IAM role exists: $ROLE_NAME"
    else
      echo "❌ IAM role not found: $ROLE_NAME"
      ERRORS=$((ERRORS + 1))
    fi
  else
    echo "❌ LambdaRoleName output missing"
    ERRORS=$((ERRORS + 1))
  fi

  # Lambda is invocable
  if [ -n "$FUNCTION_NAME" ]; then
    if aws lambda invoke --function-name "$FUNCTION_NAME" --payload '{"test": "verify"}' --cli-binary-format raw-in-base64-out /tmp/verify-output.json > /dev/null 2>&1; then
      echo "✅ Lambda is invocable"
      rm -f /tmp/verify-output.json
    else
      echo "❌ Lambda invocation failed"
      ERRORS=$((ERRORS + 1))
    fi
  fi

  # CloudWatch alarm
  if [ -n "$ALARM_NAME" ]; then
    echo "✅ CloudWatch alarm configured: $ALARM_NAME"
  else
    echo "⚠️  CloudWatchAlarmName output missing"
  fi

  # CloudWatch log group
  if aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP_NAME" --query "logGroups[?logGroupName=='$LOG_GROUP_NAME']" --output text 2>/dev/null | grep -q "$LOG_GROUP_NAME"; then
    echo "✅ CloudWatch log group exists: $LOG_GROUP_NAME"
  else
    echo "⚠️  Log group not yet created (will appear on first invocation)"
  fi
fi

echo ""

# =========================================
# 2. Auth Stack
# =========================================
echo "--- Auth Stack ($AUTH_STACK_NAME) ---"
AUTH_OUTPUTS=$(get_stack_outputs "$AUTH_STACK_NAME")

if [ $? -ne 0 ] || [ -z "$AUTH_OUTPUTS" ] || [ "$AUTH_OUTPUTS" = "null" ]; then
  echo "❌ Stack not found: $AUTH_STACK_NAME"
  ERRORS=$((ERRORS + 1))
else
  echo "✅ Stack found: $AUTH_STACK_NAME"

  USER_POOL_ID=$(get_output_value "$AUTH_OUTPUTS" "UserPoolId")
  CLIENT_ID=$(get_output_value "$AUTH_OUTPUTS" "UserPoolClientId")
  IDENTITY_POOL_ID=$(get_output_value "$AUTH_OUTPUTS" "IdentityPoolId")

  [ -n "$USER_POOL_ID" ] && echo "✅ User Pool ID: $USER_POOL_ID" || { echo "❌ UserPoolId output missing"; ERRORS=$((ERRORS + 1)); }
  [ -n "$CLIENT_ID" ] && echo "✅ User Pool Client ID: $CLIENT_ID" || { echo "❌ UserPoolClientId output missing"; ERRORS=$((ERRORS + 1)); }
  [ -n "$IDENTITY_POOL_ID" ] && echo "✅ Identity Pool ID: $IDENTITY_POOL_ID" || { echo "❌ IdentityPoolId output missing"; ERRORS=$((ERRORS + 1)); }
fi

echo ""

# =========================================
# 3. API Stack
# =========================================
echo "--- API Stack ($API_STACK_NAME) ---"
API_OUTPUTS=$(get_stack_outputs "$API_STACK_NAME")

if [ $? -ne 0 ] || [ -z "$API_OUTPUTS" ] || [ "$API_OUTPUTS" = "null" ]; then
  echo "❌ Stack not found: $API_STACK_NAME"
  ERRORS=$((ERRORS + 1))
else
  echo "✅ Stack found: $API_STACK_NAME"

  API_URL=$(get_output_value "$API_OUTPUTS" "ApiUrl")
  [ -n "$API_URL" ] && echo "✅ API URL: $API_URL" || { echo "❌ ApiUrl output missing"; ERRORS=$((ERRORS + 1)); }
fi

echo ""

# =========================================
# 4. Frontend Stack
# =========================================
echo "--- Frontend Stack ($FRONTEND_STACK_NAME) ---"
FRONTEND_OUTPUTS=$(get_stack_outputs "$FRONTEND_STACK_NAME")

if [ $? -ne 0 ] || [ -z "$FRONTEND_OUTPUTS" ] || [ "$FRONTEND_OUTPUTS" = "null" ]; then
  echo "❌ Stack not found: $FRONTEND_STACK_NAME"
  ERRORS=$((ERRORS + 1))
else
  echo "✅ Stack found: $FRONTEND_STACK_NAME"

  CF_URL=$(get_output_value "$FRONTEND_OUTPUTS" "CloudFrontUrl")
  [ -n "$CF_URL" ] && echo "✅ CloudFront URL: $CF_URL" || { echo "❌ CloudFrontUrl output missing"; ERRORS=$((ERRORS + 1)); }
fi

echo ""

# =========================================
# 5. Agent Stack (Optional)
# =========================================
echo "--- Agent Stack ($AGENT_STACK_NAME) [Optional] ---"
AGENT_OUTPUTS=$(get_stack_outputs "$AGENT_STACK_NAME")

if [ $? -ne 0 ] || [ -z "$AGENT_OUTPUTS" ] || [ "$AGENT_OUTPUTS" = "null" ]; then
  echo "⚠️  Stack not found: $AGENT_STACK_NAME"
  echo "   This is optional. Deploy with 'npm run setup' to enable AI-powered monitoring"
else
  echo "✅ Stack found: $AGENT_STACK_NAME"

  AGENT_SPACE_ID=$(get_output_value "$AGENT_OUTPUTS" "AgentSpaceId")
  SERVICE_ROLE_ARN=$(get_output_value "$AGENT_OUTPUTS" "ServiceRoleArn")
  ASSOCIATION_ID=$(get_output_value "$AGENT_OUTPUTS" "AssociationId")
  CONSOLE_URL=$(get_output_value "$AGENT_OUTPUTS" "AgentConsoleUrl")

  [ -n "$AGENT_SPACE_ID" ] && echo "✅ Agent Space ID: $AGENT_SPACE_ID" || echo "⚠️  AgentSpaceId output missing"
  [ -n "$SERVICE_ROLE_ARN" ] && echo "✅ Service Role ARN: $SERVICE_ROLE_ARN" || echo "⚠️  ServiceRoleArn output missing"
  [ -n "$ASSOCIATION_ID" ] && echo "✅ Association ID: $ASSOCIATION_ID" || echo "⚠️  AssociationId output missing"
  [ -n "$CONSOLE_URL" ] && echo "✅ Console URL: $CONSOLE_URL" || echo "⚠️  AgentConsoleUrl output missing"
fi

echo ""

# =========================================
# AWS Connectivity Check
# =========================================
echo "--- AWS Connectivity ---"
if python3 -c "import boto3; boto3.client('lambda').list_functions(MaxItems=1)" > /dev/null 2>&1; then
  echo "✅ AWS connectivity OK"
else
  echo "❌ Cannot connect to AWS"
  ERRORS=$((ERRORS + 1))
fi

echo ""
echo "========================================="
if [ $ERRORS -eq 0 ]; then
  echo "✅ Demo ready!"
  echo "========================================="
  exit 0
else
  echo "❌ $ERRORS error(s) found"
  echo "========================================="
  exit 1
fi
