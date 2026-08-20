# Quick Start Guide

Get the demo running in under 10 minutes.

## Prerequisites Check

```bash
# Check AWS CLI
aws --version                    # Need v2+
aws sts get-caller-identity      # Verify credentials

# Check Python
python3 --version                # Need 3.10+, 3.13 recommended

# Check Node.js
node --version                   # Need 22+
```

If any are missing, see [Installation](#installation) below.

## Fast Track

1. Install dependencies:
   ```bash
   npm run install:all
   ```
2. Navigate to the CDK directory:
   ```bash
   cd cdk
   ```
3. Set up the CDK environment:
   ```bash
   bash setup.sh
   ```
4. Return to the project root:
   ```bash
   cd ..
   ```
5. Deploy infrastructure (builds the frontend and deploys all stacks):
   ```bash
   npm run setup
   ```
6. Verify deployment:
   ```bash
   npm run verify
   ```

Open the **CloudFront URL** shown in the CDK deployment output to access the demo.

## Demo Flow

1. Choose **Process Order** → Order fails, incident timer starts
2. Wait 60 seconds → Amazon CloudWatch Alarm triggers (shown in UI)
3. Open the AWS DevOps Agent console → Create investigation
4. Choose **Root Cause Found** → Timer stops, shows resolution time
5. Choose **Reset Demo** → Ready for next presentation

## Cleanup

**Note**: This command destroys all AWS resources and data created by the demo, including the Amazon CloudFront distribution, Amazon S3 bucket, Amazon API Gateway REST API, AWS Lambda functions, Amazon DynamoDB table, Amazon CloudWatch alarms and logs, Amazon Cognito pools, the AWS WAF web ACL, the AWS DevOps Agent Space and its roles, and IAM roles. AWS DevOps Agent bills per second of active investigation (about $4 per 8-minute run), so run cleanup once you finish the demo.

```bash
npm run cleanup
```

---

## Detailed Setup

### Installation

#### macOS
```bash
# Install Homebrew: download the script, review it, then run it
curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o install-homebrew.sh
# Review install-homebrew.sh, then run it:
bash install-homebrew.sh

# Install dependencies
brew install python@3.13 node@22 awscli

# Configure AWS
aws configure
```

#### Linux (Ubuntu/Debian)
```bash
# Install Python (3.10+ required; check `python3 --version` after install)
sudo apt update
sudo apt install python3 python3-venv python3-pip

# Install Node.js (download the setup script, review it, then run it)
curl -fsSL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh
# Review nodesource_setup.sh, then run it:
sudo -E bash nodesource_setup.sh
sudo apt install -y nodejs

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS
aws configure
```

### Step-by-Step Deployment

#### 1. Install Project Dependencies

1. Install root dependencies (from the pinned `package.json`):
   ```bash
   npm install
   ```
2. Navigate to the CDK directory:
   ```bash
   cd cdk
   ```
3. Set up the CDK environment:
   ```bash
   bash setup.sh
   ```
4. Return to the project root:
   ```bash
   cd ..
   ```
5. Navigate to the frontend directory:
   ```bash
   cd portal/frontend
   ```
6. Install frontend dependencies (from the pinned `package.json`):
   ```bash
   npm install
   ```
7. Return to the project root:
   ```bash
   cd ../..
   ```

#### 2. Deploy AWS Infrastructure

```bash
# Bootstrap CDK (first time only)
cd cdk
source .venv/bin/activate
cdk bootstrap
cd ..

# Deploy (builds frontend and deploys all stacks)
npm run setup
```

**What Gets Created:**
- Amazon CloudFront distribution (serves frontend from Amazon S3)
- Amazon S3 bucket (frontend static assets)
- Amazon API Gateway REST API (backend endpoints)
- Amazon Cognito User Pool (authentication)
- AWS Lambda: `demo-incident-lambda`
- Amazon DynamoDB: `demo-user-data`
- Amazon CloudWatch Alarm: `demo-lambda-errors`
- AWS IAM Role: `demo-incident-lambda-role`

#### 3. Verify Deployment

```bash
npm run verify
```

Expected: `✅ Demo ready!`

#### 4. Access the Demo

Open the **CloudFront URL** from the CDK deployment output in your browser. The URL looks like:
```
https://<distribution-id>.cloudfront.net
```

## Troubleshooting

### Frontend Won't Load

```bash
# Rebuild and redeploy frontend
npm run setup
```

### Lambda Invocation Fails

```bash
# Check Lambda exists
aws lambda get-function --function-name demo-incident-lambda

# Test invocation
aws lambda invoke \
  --function-name demo-incident-lambda \
  --payload '{"test": "manual"}' \
  output.json
```

### CloudWatch Alarm Not Triggering

```bash
# Verify alarm exists
aws cloudwatch describe-alarms --alarm-names demo-lambda-errors

# Wait up to 2 minutes for evaluation period
```

### "Failed to load usage data" in DevOps Agent Console

This banner appears in the AWS DevOps Agent dashboard because the Service Role doesn't have permissions to fetch usage statistics (investigation counts, API usage, etc.). 

**This is cosmetic only and doesn't affect:**
- Creating investigations
- Analyzing logs and code
- Finding root causes
- Any demo functionality

The Service Role is intentionally scoped to only access your demo resources (Lambda, CloudWatch, DynamoDB). Usage data permissions aren't documented yet since DevOps Agent is in preview. Safe to ignore this banner.

### DevOps Agent Not Showing Incidents Automatically

AWS DevOps Agent doesn't automatically detect incidents - you must manually trigger investigations:

1. Choose the **Latest alarm** quick action button, OR
2. Create a custom investigation with the alarm ARN: `arn:aws:cloudwatch:us-east-1:123456789012:alarm:demo-lambda-errors` (replace `123456789012` with your own account ID)

The agent will then analyze logs, code, and metrics to identify the root cause.

### CDK Bootstrap Required

```bash
cd cdk
source .venv/bin/activate
cdk bootstrap
```

### Login Fails with "Incorrect username or password"

The demo password is auto-generated on each deploy. Get it from the stack outputs:

```bash
aws cloudformation describe-stacks --stack-name dev-auth \
  --query "Stacks[0].Outputs[?OutputKey=='DemoPassword'].OutputValue" \
  --output text --region us-east-1
```

If the password from the output still doesn't work (can happen after destroy + redeploy), force-reset it:

```bash
# Get the password from stack output
PASSWORD=$(aws cloudformation describe-stacks --stack-name dev-auth \
  --query "Stacks[0].Outputs[?OutputKey=='DemoPassword'].OutputValue" \
  --output text --region us-east-1)

# Get the user pool ID
POOL_ID=$(aws cloudformation describe-stacks --stack-name dev-auth \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
  --output text --region us-east-1)

# Force-set the password
aws cognito-idp admin-set-user-password \
  --user-pool-id $POOL_ID \
  --username "demo@example.com" \
  --password "$PASSWORD" \
  --permanent --region us-east-1
```

### CDK CLI Version Mismatch

If you see `Cloud assembly schema version mismatch: Maximum schema version supported is 43.x.x, but found 50.0.0`:

```bash
# Update both the CLI and the Python library to match
npm install -g aws-cdk@latest
cd cdk
source .venv/bin/activate
pip install --upgrade aws-cdk-lib constructs
```

Both must be updated together. The Python `aws-cdk-lib` generates a schema that the CLI must be able to read.

### CDK Lock File Conflict

If you see `Another CLI is currently synthing to cdk.out`:

```bash
rm -f cdk/cdk.out/.lock
```

This happens when a previous `cdk deploy` or `cdk synth` was interrupted (Ctrl+C, terminal closed, etc.).

### Clean Slate Reset

```bash
# 1. Cleanup AWS
npm run cleanup

# 2. Remove local files
rm -rf cdk/.venv portal/frontend/node_modules node_modules

# 3. Reinstall
npm install
cd cdk && bash setup.sh && cd ..
cd portal/frontend && npm install && cd ../..

# 4. Redeploy
npm run setup
```

## Key Commands

| Task | Command |
|------|---------|
| Install All | `npm run install:all` |
| Deploy | `npm run setup` |
| Verify | `npm run verify` |
| Cleanup | `npm run cleanup` |
| Preview Changes | `npm run cdk:diff` |
| Dev Frontend | `npm run dev:frontend` |

## Success Indicators

✅ `npm run verify` shows "Demo ready"  
✅ CloudFront URL loads the demo portal  
✅ "Process Order" shows error  
✅ CloudWatch Alarm triggers within 60 seconds  
✅ CloudWatch Alarm status visible in portal  

## Next Steps

- **Practice the demo** 2-3 times
- **Configure AWS DevOps Agent** (optional) — see [README](./README.md#post-deploy-configure-devops-agent-web-app) for setup instructions
- **Customize for your audience**

## Support

- **Architecture Details**: See [ARCHITECTURE.md](./ARCHITECTURE.md)
- **AWS DevOps Agent**: https://docs.aws.amazon.com/devopsagent/latest/userguide/getting-started-with-aws-devops-agent.html

## Conclusion

Once `npm run verify` reports the demo is ready, the AWS DevOps Agent demo is deployed and ready to showcase automated incident detection and diagnosis. Practice the demo flow a few times to get comfortable with the timing and the agent's responses. When you are finished, run `npm run cleanup` to remove all AWS resources. For the technical architecture and security model, see [ARCHITECTURE.md](./ARCHITECTURE.md) and [SECURITY.md](./SECURITY.md).
