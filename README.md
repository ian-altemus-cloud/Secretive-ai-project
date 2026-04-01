# Secretive AI Platform

Production AI-powered Instagram DM automation built for a real multi-location beauty business in Southern California.

The business owner was handling every Instagram DM manually. Pricing questions, availability requests, booking inquiries, all coming in at all hours. Respond late and the booking goes somewhere else. I built this to solve that.

## What It Does

When a client DMs the salon's Instagram account:

1. Meta fires a webhook to API Gateway
2. The request is validated with HMAC SHA256 signature verification
3. The message is routed to SQS to decouple intake from processing
4. The Fargate container consumes the message and retrieves conversation history from DynamoDB
5. Claude generates a response in the salon's voice, warm, professional, conversion-focused
6. The response goes back to the client via the Meta Graph API
7. The interaction is logged to Google Sheets for business attribution
8. Prometheus metrics are scraped and visualized in Grafana

No human in the loop. The owner wakes up to booked appointments.

## Architecture

```
Instagram DM
     |
     v
Meta Webhook
     |
     v
API Gateway (REST)  [HMAC SHA256 Signature Validation]
     |
     v
SQS Queue  [Dead Letter Queue]
     |
     v
ECS Fargate (Flask App)  [Private Subnet]
     |
     +---- DynamoDB (Conversation State)
     +---- Claude via Anthropic API / AWS Bedrock
     +---- Google Sheets (Attribution Logging)
     +---- Prometheus Metrics (port 8000)
                |
                v
           Grafana Dashboard
```

VPC architecture: public subnets for ALB and NAT Gateway, private subnets for Fargate compute and the Prometheus/Grafana observability stack. DynamoDB accessed via VPC Gateway endpoint.

## Stack

| Layer | Technology |
|---|---|
| Cloud | AWS (us-east-1) |
| Infrastructure as Code | Terraform |
| Compute | ECS Fargate |
| Messaging | SQS + Dead Letter Queue |
| Database | DynamoDB (PAY_PER_REQUEST) |
| AI | Anthropic Claude / AWS Bedrock (inference profile) |
| Secrets | AWS Secrets Manager |
| CI/CD | GitHub Actions with OIDC authentication |
| Observability | Prometheus + Grafana on ECS |
| Logging | CloudWatch + Google Sheets |
| Language | Python (Flask) |
| Container | Docker (linux/amd64) |

## Infrastructure

40 AWS resources across 7 Terraform modules:

**VPC module** — Custom VPC, public/private subnets across 2 AZs, IGW, NAT Gateway, route tables

**Security Groups module** — ALB SG (443/80 ingress), Fargate SG (ALB-only ingress via security group reference), observability SG (ports 3000/9090)

**SQS module** — Main queue, DLQ, redrive policy (3 max receives)

**DynamoDB module** — Conversation state table, `instagram_user_id` partition key, PAY_PER_REQUEST billing

**ECR module** — Image tag immutability, scan on push

**Secrets Manager module** — Hierarchical `/secretive/dev/` path naming for IAM scoping, Meta API token, Google Sheets credentials, Anthropic API key

**Fargate module** — ECS cluster, task definition, service, execution role, task role with scoped inline policies, CloudWatch log group

All infrastructure is managed as code with S3 remote state backend and DynamoDB state locking.

## Application Layer

`webhook_handler.py` handles Meta webhook verification, HMAC SHA256 signature validation on every request, SQS message routing, and a three-thread architecture running Flask, the SQS consumer loop, and the Prometheus metrics server simultaneously.

`bedrock_client.py` implements a provider abstraction layer. The `AI_PROVIDER` environment variable switches between the direct Anthropic API and AWS Bedrock inference profile. Bedrock infrastructure stays intact and one env var change switches back when the account usage history matures.

`conversation_store.py` handles DynamoDB read/write, conversation history threading, and role-labeled message structure for multi-turn context.

`sheets_logger.py` handles Google Sheets attribution logging with a separated authentication function, Secrets Manager credential retrieval, and a seven-column conversation log.

`metrics.py` defines Prometheus counters and histograms with location labels on the DM counter and latency histograms for AI provider response time and Sheets logging.

## Security Design

Security was designed into the architecture from the first line of Terraform, not added after the fact.

**Zero stored credentials.** OIDC authentication between GitHub Actions and AWS. No AWS keys in GitHub Secrets. Nothing stored, nothing that can leak, nothing that rotates manually.

**Secrets Manager for all sensitive values.** Meta API token, Google Sheets service account, and Anthropic API key all live in Secrets Manager with hierarchical path naming for IAM scoping. Credentials never leave the AWS boundary.

**HMAC SHA256 on every webhook request.** Every incoming request is validated against Meta's signature before any processing begins.

**IAM least privilege throughout.** Separate scoped inline policies on the ECS task role with specific resource ARNs. Execution role and task role are explicitly separated. 10 scoped managed policies on the GHA role. When the IAM policy quota was hit during development, the solution was to consolidate policies rather than broaden them. The system is designed to look like production, not a solo project.

**VPC isolation.** Fargate runs in private subnets with no direct internet exposure. All outbound traffic routes through NAT Gateway. DynamoDB traffic stays inside the AWS network via Gateway endpoint.

## CI/CD Pipeline

```
Push to main
     |
     +-- terraform fmt -check
     +-- terraform init
     +-- terraform validate
     +-- terraform plan -out=tfplan (artifact upload for deterministic apply)
     |
     v
Manual Approval Gate
     |
     v
terraform apply (from saved plan artifact)
```

OIDC trust policy scoped to the `main` branch using `StringLike` with wildcard to support environment-scoped job tokens.

## Observability

Prometheus runs on ECS Fargate in a dedicated private subnet with a custom scrape config targeting the Flask app on port 8000 via Cloud Map service discovery.

Grafana dashboard tracks business metrics:

- `booking_link_sent_total` — conversion tracking by location
- `dm_response_latency` — AI provider response time
- `escalation_total` — conversations routed to human
- `meta_api_errors_total` — webhook delivery failures

CloudWatch covers container logs, ECS service health, and task-level metrics.

## Key Engineering Decisions

**Why SQS between API Gateway and Fargate?**

Meta's webhook has a hard timeout. Processing synchronously means a DynamoDB read, an AI invocation, and a Sheets write all happen before the response goes back. Any one of those can exceed the timeout, which causes Meta to retry and potentially deliver duplicate messages to the client. For a nail salon DM, sub-second response time has zero business value. Message reliability has high business value. A dropped message is a lost booking. SQS decouples intake from processing, guarantees delivery, and lets the processing layer scale independently of the intake layer.

**Why Secrets Manager over GitHub Secrets?**

Every credential this system needs at runtime lives inside AWS. The Fargate task runs inside AWS. There is no good reason for credentials to cross the AWS boundary at all. Secrets Manager keeps everything inside the boundary with IAM-native access control and CloudTrail audit logging on every retrieval. The question I kept asking was: what is the point of letting the secrets leave AWS if they never need to?

**Why OIDC over stored credentials?**

Stored credentials rotate manually, can leak, and every rotation is a potential gap. OIDC issues short-lived tokens scoped to exactly what the specific workflow needs. The GitHub Actions workflow requests a token, AWS validates the identity and issues temporary credentials, the workflow does its job, the credentials expire. Nothing persists.

**Why the provider abstraction layer?**

AWS Bedrock is the correct production target. IAM-native authentication, VPC endpoint, CloudTrail logging on every invocation, no hardcoded API keys anywhere. New AWS accounts face quota restrictions on Bedrock that require usage history to resolve. Rather than block on an AWS Support case indefinitely, the abstraction layer bridges the gap cleanly. One environment variable switches between providers. The architecture is right. The operational constraint is temporary.

## What's Next

**Phase 2 — Follow-up System**

Clients who go quiet after an initial conversation represent recoverable bookings. A 24-hour contextual follow-up based on what they were asking about, a 3-4 week soft re-engagement, and a permanent opt-out flag in DynamoDB. EventBridge scheduler triggers a Lambda function for the timing logic.

**Phase 3 — System Prompt Configurability**

Move the system prompt to Parameter Store or DynamoDB so the business owner can adjust the AI's voice without touching a deployment.

**Phase 4 — Multi-location Routing**

Location-specific context and escalation paths for Newport Beach, Beverly Hills, and Santa Monica.

## Local Development

```bash
git clone https://github.com/ian-altemus-cloud/Secretive-ai-project.git
pip install -r app/requirements.txt
docker-compose up
```

## Infrastructure Deployment

```bash
cd terraform/envs/dev
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Remote state is managed via S3 with versioning enabled and DynamoDB state locking.

## About

Built by **Ian Altemus** — Cloud & Infrastructure Engineer

This project solves a real business problem for a real client. The business owner was skeptical. After seeing it live, the response was: "No, wow. This is actually good."

That is the only metric that matters.

[LinkedIn](https://linkedin.com/in/ian-altemus-cloud) · [GitHub](https://github.com/ian-altemus-cloud) · [Pulse](https://github.com/ian-altemus-cloud/Pulse)