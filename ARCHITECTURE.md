<!-- Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. -->
<!-- SPDX-License-Identifier: MIT-0 -->
# AWS DevOps Agent Demo - Architecture

## System Overview

```mermaid
graph TB
    subgraph "AWS Cloud (us-east-1)"
        CF["☁️ Amazon CloudFront<br/>Distribution"]
        S3["📦 Amazon S3 Bucket<br/>React SPA"]
        APIGW["🔌 Amazon API Gateway<br/>REST API"]
        COG["🔐 Amazon Cognito<br/>User Pool"]
        LAM["⚡ AWS Lambda<br/>demo-incident-lambda"]
        DDB["🗄️ Amazon DynamoDB<br/>demo-user-data"]
        CW["📊 Amazon CloudWatch<br/>Logs + Alarm"]
        AGENT["🤖 AWS DevOps Agent"]
    end

    BROWSER["🌐 Browser"] -->|"HTTPS"| CF
    CF -->|"OAC"| S3
    BROWSER -->|"Direct API call<br/>with JWT"| APIGW
    APIGW -->|"Validates JWT"| COG
    APIGW -->|"Invokes"| LAM
    LAM -->|"update_item ❌"| DDB
    LAM -->|"Error logs"| CW
    CW -->|"Alarm triggers"| AGENT
    AGENT -->|"Analysis in"| CONSOLE["🖥️ AWS Console"]
```

## The Bug Explained

### What's Wrong

The Lambda function uses **`update_item()`** with **`attribute_exists(id)`** condition to store new orders:

```python
# BROKEN CODE (current)
table.update_item(
    Key={'id': order_id},
    UpdateExpression='SET order_data = :data, #s = :status',
    ConditionExpression='attribute_exists(id)',  # ❌ Requires item to exist!
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={':data': json.dumps(event), ':status': 'processed'},
)
```

### Why It Fails

1. Each order gets a **unique ID** from `context.aws_request_id`
2. This ID has **never been written** to DynamoDB
3. `update_item()` with `attribute_exists()` **requires the item to already exist**
4. Result: **ConditionalCheckFailedException** on every single order

### The Fix

Change to **`put_item()`** for new orders:

```python
# FIXED CODE
table.put_item(
    Item={
        'id': order_id,
        'order_data': json.dumps(event),
        'status': 'processed',
        'created_at': datetime.now().isoformat(),
    }
)
```

### Why This is Realistic

This bug represents a common production error:
- Developer intended to update existing orders
- Forgot that new orders don't exist yet
- Condition check prevents the operation
- 100% failure rate makes it obvious in demo

## Component Details

This section describes each component of the demo and how it is configured.

### Frontend (React + Vite)
- **Technology**: React 18, TypeScript, Tailwind CSS
- **Hosting**: Amazon CloudFront distribution serving static assets from Amazon S3
- **Build Tool**: Vite 4
- **Location**: `portal/frontend/`
- **Configuration**: Runtime injection via `/runtime-config.js` (deployed by CDK AwsCustomResource to S3)
- **Components Used in UI**:
  - ProcessOrderButton - "Process Order" button
  - ResetButton - "Reset Demo" button
  - BusinessDiagram - Customer flow diagram
  - ArchitectureDiagram - AWS technical diagram
  - IncidentBanner - Shows incident status and timer


### Backend API (API Gateway + Lambda)
- **API**: Amazon API Gateway REST API
- **Compute**: AWS Lambda (Python 3.13 runtime)
- **Authentication**: Amazon Cognito User Pool with JWT authorizer
- **CORS**: Configured for the CloudFront origin
- **Location**: `cdk/lib/stacks/api_stack.py`
- **Endpoints**:
  - `POST /process-order` - Process customer order (invokes target Lambda)
  - `GET /alarm-status` - Get CloudWatch Alarm state (polled during incident)

### Authentication (Cognito)
- **Service**: Amazon Cognito User Pool
- **Authorizer**: JWT authorizer on API Gateway
- **Identity Pool**: Federated identity for AWS credential exchange
- **Location**: `cdk/lib/stacks/auth_stack.py`

### Target AWS Lambda
- **Runtime**: Python 3.13
- **Name**: demo-incident-lambda
- **Timeout**: 10 seconds
- **Memory**: 128 MB
- **Environment**: `TABLE_NAME=demo-user-data`
- **Bug**: Uses `update_item()` with `attribute_exists()` condition on new orders
- **Result**: ConditionalCheckFailedException on every order

### AWS DevOps Agent
- **Purpose**: Automated incident detection
- **Capabilities**:
  - Error detection in CloudWatch Logs
  - Multi-service investigation
  - Root cause analysis
  - Displays analysis in AWS Console

## Data Flow

### 1. Error Trigger Flow

```mermaid
sequenceDiagram
    actor User
    participant CF as CloudFront
    participant S3 as S3 Bucket
    participant COG as Cognito
    participant APIGW as API Gateway
    participant LAM as Lambda
    participant DDB as DynamoDB
    participant CW as CloudWatch

    User->>CF: Access demo URL
    CF->>S3: Fetch React SPA
    S3-->>CF: index.html + assets
    CF-->>User: Render portal

    User->>COG: Sign in (demo@example.com)
    COG-->>User: JWT tokens

    User->>APIGW: POST /process-order (JWT)
    APIGW->>COG: Validate JWT
    COG-->>APIGW: ✅ Valid
    APIGW->>LAM: Invoke handler

    LAM->>LAM: Generate unique order ID
    LAM->>DDB: update_item(attribute_exists)
    DDB-->>LAM: ❌ ConditionalCheckFailedException

    LAM->>CW: Error logged
    LAM-->>APIGW: 500 Error
    APIGW-->>User: "Order Processing Failed"
```

### 2. AWS DevOps Agent Detection Flow

```mermaid
sequenceDiagram
    participant CW as CloudWatch Logs
    participant ALARM as CloudWatch Alarm
    participant AGENT as DevOps Agent
    participant CONSOLE as AWS Console

    CW->>ALARM: Error metric breaches threshold
    Note over ALARM: Triggers within 60 seconds

    ALARM->>AGENT: Alarm state: ALARM

    AGENT->>CW: Analyze error logs
    AGENT->>AGENT: Check Lambda code patterns
    AGENT->>AGENT: Review DynamoDB operations
    AGENT->>AGENT: Correlate across services

    Note over AGENT: Root cause: update_item()<br/>on non-existent items

    AGENT->>CONSOLE: Display analysis + recommendation
    Note over CONSOLE: Fix: Change to put_item()
```

### 3. Manual Fix Flow (Outside Demo Portal)

The demo shows the problem detection. The fix is demonstrated manually:

```mermaid
graph LR
    A["Presenter explains<br/>the bug"] --> B["Show DevOps Agent<br/>recommendation"]
    B --> C["Explain: change<br/>update_item → put_item"]
    C --> D["(Optional) Apply fix<br/>via Console or CLI"]
```

**Note:** The demo focuses on detection and diagnosis, not automated remediation.

### 4. Demo Reset Flow

```mermaid
graph LR
    A["Choose Reset Demo"] --> B["Frontend clears<br/>local state"]
    B --> C["Incident timer<br/>resets"]
    C --> D["Portal returns<br/>to clean state"]
    D --> E["Ready for next<br/>demonstration"]
```

## Deployment Architecture

### CDK Deployment

```mermaid
graph TB
    DEV["💻 Developer Machine<br/>npm run setup"]
    APP["cdk/app.py"]

    subgraph STAGE ["ApplicationStage (dev)"]
        direction TB
        DEMO["🟢 DemoStack<br/>(dev-demo)"]
        AUTH["🟢 AuthStack<br/>(dev-auth)"]
        API["🟡 ApiStack<br/>(dev-api)"]
        FE["🟡 FrontendStack<br/>(dev-frontend)"]
        AGT["🟢 AgentStack<br/>(dev-agent)"]
    end

    DEV --> APP --> STAGE

    DEMO --- D1["DynamoDB table"]
    DEMO --- D2["Lambda function (with bug)"]
    DEMO --- D3["IAM roles"]
    DEMO --- D4["CloudWatch Alarm"]

    AUTH --- A1["Cognito User Pool + Client"]
    AUTH --- A2["Cognito Identity Pool"]
    AUTH --- A3["Demo user credentials"]

    API --- P1["API Gateway REST API"]
    API --- P2["Cognito JWT Authorizer"]
    API --- P3["Lambda integration"]
    API --- P4["CORS configuration"]

    FE --- F1["S3 bucket + CloudFront + OAC"]
    FE --- F2["Build & deploy frontend"]
    FE --- F3["runtime-config.js → S3"]
    FE --- F4["Update Cognito callbacks"]
    FE --- F5["Update Lambda ALLOWED_ORIGINS"]

    AGT --- G1["Agent Space"]
    AGT --- G2["IAM Service + Operator Roles"]
    AGT --- G3["Account Association"]

    AUTH --> API
    DEMO --> API
    AUTH --> FE
    API --> FE
    DEMO --> FE
```

🟢 = independent (no dependencies) · 🟡 = depends on other stacks

### Runtime Architecture

```mermaid
graph TB
    BROWSER["🌐 Browser"]

    subgraph AWS ["AWS Cloud (us-east-1)"]
        subgraph HOSTING ["Static Hosting"]
            CF["☁️ CloudFront Distribution<br/>Default: S3 origin<br/>Error pages: 403/404 → /index.html"]
            S3["📦 S3 Bucket<br/>index.html · assets/* · runtime-config.js"]
        end

        subgraph BACKEND ["Backend"]
            APIGW["🔌 API Gateway REST API<br/>POST /process-order<br/>GET /alarm-status"]
            COG["🔐 Cognito<br/>User Pool · Client · Identity Pool"]
            LAM["⚡ Lambda<br/>demo-incident-lambda<br/>❌ Fails: ConditionalCheckFailedException"]
        end

        subgraph DATA ["Data & Monitoring"]
            DDB["🗄️ DynamoDB<br/>demo-user-data"]
            CW["📊 CloudWatch Logs<br/>/aws/lambda/demo-*"]
            ALARM["🔔 CloudWatch Alarm<br/>demo-lambda-errors"]
        end

        AGENT["🤖 AWS DevOps Agent"]
    end

    BROWSER -->|"HTTPS"| CF
    CF -->|"OAC"| S3
    BROWSER -->|"Direct API call with JWT"| APIGW
    APIGW -->|"Validate JWT"| COG
    APIGW -->|"Invoke"| LAM
    LAM -->|"update_item ❌"| DDB
    LAM -->|"Error logs"| CW
    CW --> ALARM
    ALARM --> AGENT
```



## Security Architecture

> For the full security documentation including threat model, data classification, key management, and shared responsibility model, see [SECURITY.md](SECURITY.md).

### Authentication & Authorization

```mermaid
sequenceDiagram
    actor User as Browser
    participant COG as Cognito User Pool
    participant APIGW as API Gateway
    participant LAM as Lambda
    participant IDP as Cognito Identity Pool

    User->>COG: Sign in (email + password)
    COG-->>User: JWT tokens (ID + Access)

    User->>APIGW: API request + JWT
    APIGW->>COG: Validate JWT
    COG-->>APIGW: ✅ Valid
    APIGW->>LAM: Invoke with IAM role
    LAM-->>APIGW: Response
    APIGW-->>User: API response

    Note over User,IDP: Optional: AWS credential exchange
    User->>IDP: Exchange JWT
    IDP-->>User: Temporary AWS credentials
```

### AWS IAM Permissions

> **Customer Responsibility**: You are responsible for defining and maintaining IAM policies that follow the principle of least privilege. Review and update these policies regularly to verify they grant only the minimum permissions required.

```mermaid
graph TB
    ROLE["demo-incident-lambda-role<br/>Trust: lambda.amazonaws.com"]

    subgraph MANAGED ["Managed Policy"]
        EXEC["AWSLambdaBasicExecutionRole"]
        EXEC --- L1["logs:CreateLogGroup"]
        EXEC --- L2["logs:CreateLogStream"]
        EXEC --- L3["logs:PutLogEvents"]
    end

    subgraph INLINE ["Inline Policy: DynamoDB Access"]
        DDB["Resource: demo-user-data table"]
        DDB --- D1["dynamodb:PutItem"]
        DDB --- D2["dynamodb:GetItem"]
        DDB --- D3["dynamodb:UpdateItem"]
    end

    ROLE --> MANAGED
    ROLE --> INLINE
```

### Network Security

**AWS-managed security**: Lambda execution environment, CloudFront TLS termination, API Gateway DDoS protection.
**Customer-configured security**: API Gateway HTTPS enforcement, S3 bucket access policies, CloudFront distribution settings, CORS origin allowlists.

- **CloudFront**: HTTPS only, TLS 1.2+
- **S3**: Private bucket, accessible only via CloudFront OAC
- **API Gateway**: HTTPS only, Cognito JWT authorization
- **Lambda**: Runs in AWS-managed VPC

## CORS Architecture

The frontend (served from CloudFront) makes cross-origin requests directly to API Gateway. CORS is handled by a three-layer pattern where each layer serves a distinct purpose:

```mermaid
sequenceDiagram
    participant B as Browser
    participant AG as API Gateway
    participant L as Lambda

    Note over B,L: Layer 1 — Preflight (OPTIONS)
    B->>AG: OPTIONS /process-order<br/>Origin: https://d1abc.cloudfront.net
    AG-->>B: 200 OK<br/>Access-Control-Allow-Origin: *<br/>(no credentials, wildcard is safe)

    Note over B,L: Layer 2 — Actual Request (success path)
    B->>AG: POST /process-order<br/>Origin: https://d1abc.cloudfront.net<br/>Authorization: Bearer <JWT>
    AG->>L: Invoke handler(event, context)
    L-->>AG: 200 OK<br/>Access-Control-Allow-Origin: https://d1abc.cloudfront.net<br/>Access-Control-Allow-Credentials: true
    AG-->>B: 200 OK (exact origin, with credentials)

    Note over B,L: Layer 3 — API Gateway error (auth failure, throttle)
    B->>AG: POST /process-order<br/>Origin: https://d1abc.cloudfront.net<br/>Authorization: Bearer <expired>
    AG-->>B: 401 Unauthorized<br/>Access-Control-Allow-Origin: *<br/>(Lambda never executed)
```

### Why Three Layers?

| Layer | Origin Header | Why |
|-------|--------------|-----|
| Preflight (OPTIONS) | `*` wildcard | CloudFront URL doesn't exist when ApiStack is created (cyclic dependency). Wildcard on preflight is safe per CORS spec — browsers never send credentials on preflight requests. |
| Lambda responses | Exact origin match | The real security enforcement. Lambda reads `ALLOWED_ORIGINS` env var, checks the request's `Origin` header against the list, and returns the exact origin only if it matches. Supports `Access-Control-Allow-Credentials: true`. |
| Gateway error responses (4xx/5xx) | `*` wildcard | When API Gateway rejects a request itself (expired JWT, throttling, malformed request), Lambda never executes and can't set CORS headers. Without wildcard headers on these responses, the browser blocks them entirely and the frontend can't display error messages. Only generic error codes are exposed. |

### Allowed Origins

Origins are configured in two phases during deployment:

1. `ApiStack` creates both Lambdas with an empty `ALLOWED_ORIGINS` (the CloudFront URL does not exist yet at this point)
2. `FrontendStack` updates `ALLOWED_ORIGINS` via `AwsCustomResource` to the CloudFront distribution URL after it's created

At runtime, both Lambdas accept requests only from the CloudFront URL (production). There is no local-development origin.

## Monitoring & Observability

### What Gets Monitored

```mermaid
graph LR
    LAM["⚡ Lambda Function"]
    LAM -->|"Invocations<br/>Errors<br/>Duration"| CW["📊 CloudWatch Logs<br/>/aws/lambda/demo-incident-lambda"]
    CW -->|"Error count ≥ 1"| ALARM["🔔 CloudWatch Alarm<br/>demo-lambda-errors"]
    ALARM -->|"ALARM state"| AGENT["🤖 AWS DevOps Agent"]
    AGENT --> A1["Error detection"]
    AGENT --> A2["Root cause analysis"]
    AGENT --> A3["AWS Console display"]
```

### Logs Location

- **Lambda Logs**: `/aws/lambda/demo-incident-lambda`
- **API Gateway Logs**: `/aws/apigateway/<api-id>` (1 week retention)
- **Frontend Logs**: Browser console

## CDK Stack Dependencies

```mermaid
graph TB
    DEMO["🟢 DemoStack (dev-demo)<br/>Lambda · DynamoDB · CloudWatch Alarm"]
    AUTH["🟢 AuthStack (dev-auth)<br/>Cognito User Pool · Identity Pool · Demo user"]
    API["🟡 ApiStack (dev-api)<br/>API Gateway · Cognito authorizer · Lambda integration"]
    FE["🟡 FrontendStack (dev-frontend)<br/>S3 · CloudFront · runtime-config.js<br/>Post-deploy: update Cognito callbacks + ALLOWED_ORIGINS"]
    AGT["🟢 AgentStack (dev-agent)<br/>Agent Space · Service Role · Operator Role"]

    AUTH --> API
    DEMO --> API
    AUTH --> FE
    API --> FE
    DEMO --> FE
```

🟢 = independent · 🟡 = has dependencies (arrows show what it depends on)

## Conclusion

This architecture combines Amazon CloudFront and Amazon S3 for static hosting, Amazon API Gateway and AWS Lambda for the backend, Amazon Cognito for authentication, Amazon DynamoDB for storage, and Amazon CloudWatch with AWS DevOps Agent for monitoring and automated incident diagnosis. The intentional `update_item()`/`attribute_exists()` bug gives AWS DevOps Agent a realistic, repeatable failure to detect and diagnose.

Next steps:
- To deploy the demo, see [QUICKSTART.md](./QUICKSTART.md).
- For the security model, threat analysis, and shared responsibility details, see [SECURITY.md](./SECURITY.md).
- For an overview and cost estimates, see [README.md](./README.md).
