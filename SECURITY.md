# AWS DevOps Agent Demo — Security Considerations

## Reporting a security issue

If you discover a potential security issue in this project, we ask that you notify AWS/Amazon Security via our [vulnerability reporting page](https://aws.amazon.com/security/vulnerability-reporting/) or directly via email to aws-security@amazon.com. Please do **not** create a public GitHub issue.

## This is sample code

This is sample code, for non-production usage. You should work with your security and legal teams to meet your organizational security, regulatory and compliance requirements before deployment.

This project **intentionally contains a bug** — the order-processing AWS Lambda function uses `update_item()` with an `attribute_exists()` condition on brand-new orders, so every order fails. This is the point of the demo: it gives AWS DevOps Agent a realistic failure to detect and diagnose. The project is **not intended for production use**. Deploy it only in isolated, ephemeral AWS accounts and tear it down after use (`npm run cleanup`).

## Security considerations

Because this is a demonstration system, it makes deliberate trade-offs you should understand before deploying it anywhere:

- The order Lambda is designed to fail (core demo behavior).
- A demo user is auto-created and its generated password is surfaced via an AWS CloudFormation output — convenient for a short-lived demo, not appropriate for production.
- The Lambda function logs full request payloads to Amazon CloudWatch for demo visibility.
- MFA is not enforced and Amazon DynamoDB point-in-time recovery is disabled.

Review and harden these (and apply your own controls) before any non-demo use.

## Known IAM exceptions

Two intentional IAM patterns in this sample are flagged by automated security rubrics. They are deliberate and documented here as known limitations:

- **Demo password in a CloudFormation output** (`auth_stack.py`): the auto-generated demo-user password is surfaced via a `CfnOutput` so presenters can sign in quickly. CloudFormation outputs are **not encrypted** and are visible in the AWS Console and CLI. This is acceptable only for short-lived, isolated demo accounts. For production, store credentials in [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html) and never expose them in outputs.
- **`Resource: "*"` on AWS Support API actions** (`agent_stack.py`): the operator role grants `support:DescribeCases`, `support:InitiateChatForCase`, and `support:DescribeSupportLevel` on `"*"`. AWS Support API actions do not support resource-level permissions (see the [service authorization reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_awssupport.html)), so the wildcard is unavoidable. Access is constrained to `us-east-1` via an `aws:RequestedRegion` condition.
- **Defense-in-depth DENY on the unauthenticated identity-pool role** (`auth_stack.py`): a `Deny` statement on `Action: "*"` / `Resource: "*"` is attached as a second layer. The identity pool already sets `allow_unauthenticated_identities=False`; the blanket deny is intentional belt-and-suspenders, not a grant.

## Shared responsibility

This sample runs on AWS managed services. Under the [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/), AWS secures the underlying cloud infrastructure while you remain responsible for how you configure and operate what you deploy — IAM permissions, data handling, network controls, and account security.

## Conclusion

This demo is built for short-lived, isolated environments to showcase AWS DevOps Agent capabilities. Deploy it only in non-production accounts, review the security considerations and known IAM exceptions above before deploying, and tear down the resources immediately after use (`npm run cleanup`). For production implementations, work with your security team to apply appropriate hardening and controls.
