# P2.5 — AWS Bedrock Primer

Standalone exposure to AWS Bedrock for Claude, slotted between **P2 Pinecone variant** and **P13 MatchScout V2 Agent SDK rebuild** so the AWS console + IAM + cross-region inference concepts are already familiar before P13's full Bedrock-on-Agent-SDK build.

## What this primer demonstrates

1. **List Claude models** available in your Bedrock account + region
2. **List cross-region inference profiles** (the `us.` / `eu.` prefixed IDs that route across regions)
3. **Invoke Claude Sonnet 4.6 via Bedrock** with `boto3` + the Bedrock-wrapped Messages API request body
4. **Invoke the same prompt via direct Anthropic API** for side-by-side comparison
5. **Compare** latency, token counts, stop reasons, USD cost — same model, two access paths

## Why this exercise exists in the curriculum

- **Direct Anthropic API is dev positioning. Bedrock is production positioning.**
- Enterprises route through Bedrock for: IAM consolidation, billing rollup, VPC peering, CloudTrail audit, compliance (SOC2 / HIPAA / FedRAMP), data residency
- In enterprise AI Engineer interviews, "I built this on Bedrock" lands harder than "I called the Anthropic API"
- This primer is the **single-session AWS-console familiarity step** — P13 then does the real build (Claude Agent SDK + subagents + Reflexion + Memory tool) on top of Bedrock

## Prerequisites (one-time setup)

### 1. AWS account with Bedrock access
- Sign up at aws.amazon.com if you don't have one (free tier covers our usage)
- Navigate to https://console.aws.amazon.com/bedrock

### 2. Request model access (one-click step in Bedrock console)
- In the Bedrock console sidebar: **Model access** → **Request model access**
- Check the Anthropic Claude Sonnet 4.6 box (and other Claude models if you want broader access)
- Approval is typically **instant for Anthropic models** in US regions

### 3. IAM identity with Bedrock permissions
Create an IAM user (or role) with this minimum policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel",
                "bedrock:ListInferenceProfiles"
            ],
            "Resource": "*"
        }
    ]
}
```

### 4. Configure AWS credentials (one of)
```bash
# Option A — aws cli writes to ~/.aws/credentials
aws configure

# Option B — environment vars (good for .env)
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1

# Option C — if running on EC2/Lambda, attach IAM role to the resource
```

### 5. Install Python deps
```bash
cd /Users/rajeshramani/ai/ai_engineer_program
source .venv/bin/activate
pip install boto3 anthropic
```

## Running

```bash
# Default: list models + run comparison call
python p2_5_bedrock_primer/bedrock_primer.py

# Just see what's accessible
python p2_5_bedrock_primer/bedrock_primer.py --list-only
```

## Key concepts to take away

### `bedrock` vs `bedrock-runtime` — two clients

- **`boto3.client("bedrock", ...)`** — control plane. List models, request access, describe inference profiles. Read-mostly.
- **`boto3.client("bedrock-runtime", ...)`** — data plane. Invoke models. This is where the tokens flow.

Two separate clients, same AWS credentials. Common confusion when starting.

### Cross-region inference profiles

System-defined profiles prefixed `us.` or `eu.` (e.g. `us.anthropic.claude-sonnet-4-6-20250514-v1:0`) route invocations across multiple regions transparently. Typical benefits:

- 2–3× effective rate limits at no cost difference
- Higher resilience (one region's outage doesn't kill the call)
- Better tail latency

The plain region-pinned ID (no `us.` prefix) pins to the region in your client config. Production almost always uses cross-region.

### The Bedrock request envelope

Direct Anthropic API:
```python
client.messages.create(model="claude-sonnet-4-6", max_tokens=256,
                       messages=[{"role": "user", "content": "..."}])
```

Bedrock equivalent (note the `anthropic_version` line — Bedrock-specific):
```python
runtime.invoke_model(
    modelId="us.anthropic.claude-sonnet-4-6-20250514-v1:0",
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",   # ← required envelope marker
        "max_tokens": 256,
        "messages": [{"role": "user", "content": "..."}]
    }).encode("utf-8"),
    contentType="application/json",
    accept="application/json",
)
```

The Messages API body is the same. Bedrock wraps it with a marker so it can support multiple model families through one envelope.

### Pricing parity

For Claude models, Bedrock pricing matches direct Anthropic API on a per-token basis. You're not paying a Bedrock surcharge — you're paying for AWS-side conveniences (IAM, billing rollup, audit logs).

### Cost tracking pattern

The primer demonstrates the cost-tracking pattern you'll reuse in production:

```python
input_tokens  = response["usage"]["input_tokens"]
output_tokens = response["usage"]["output_tokens"]
cost_usd = input_tokens * 3.00 / 1e6 + output_tokens * 15.00 / 1e6
```

Persist this on every call. Aggregate by tenant, model version, prompt version. It's the same pattern P7 MatchScout uses with the `cost_usd` column.

## What's next

After this primer:

→ **P13 — MatchScout V2 Agent SDK rebuild on Bedrock**
The full build. Claude Agent SDK + subagents (history / reasoner / fact-checker / critic) + Anthropic Memory tool + Reflexion, all running through Bedrock. CloudWatch Logs for traces. Bedrock Guardrails as the safety layer. Bedrock vs direct-API cost comparison at workload scale.

This primer is the warm-up; P13 is the headline build.
