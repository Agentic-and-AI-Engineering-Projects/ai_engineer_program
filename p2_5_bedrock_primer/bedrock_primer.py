"""
AWS Bedrock primer — getting Claude calls to work via Bedrock vs direct Anthropic API.

What this primer demonstrates:
1. List Claude models accessible to your Bedrock account
2. Call Claude Sonnet 4.6 via Bedrock with the SAME prompt as a direct Anthropic call
3. Compare: latency, token counts, response shape, USD cost
4. Walk through the IAM policy + model-access flow

Why this matters for the curriculum:
- Direct Anthropic API is dev-environment positioning. Bedrock is production positioning.
- Enterprises route through Bedrock for IAM consolidation, billing rollup, VPC peering,
  CloudTrail audit, compliance (SOC2 / HIPAA / FedRAMP), and data residency.
- "I built this on Bedrock" lands harder in enterprise interviews than "I called the API directly".

Prerequisites:
1. AWS account with Bedrock enabled.
2. Model access requested + approved for Claude Sonnet 4.6 (a one-click step in the
   Bedrock console: aws.amazon.com/bedrock → Model access → Request model access).
3. IAM identity with the following minimum policy:

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

4. AWS credentials configured (one of):
     - `aws configure` (writes to ~/.aws/credentials)
     - Environment vars: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
     - IAM role (if running on EC2 / Lambda / similar)

5. Python deps:
     pip install boto3 anthropic

Cross-region inference profiles:
   Bedrock supports "system-defined" inference profiles (prefixed `us.` or `eu.`) that
   route invocations across multiple regions for higher throughput and resilience.
   For Claude Sonnet 4.6, the cross-region ID is typically:
     us.anthropic.claude-sonnet-4-6-20250514-v1:0
   The plain region-pinned ID is:
     anthropic.claude-sonnet-4-6-20250514-v1:0
   Cross-region typically gives 2-3x effective rate limits at no cost difference.

Usage:
    # Default: list models, run comparison call, show side-by-side
    python bedrock_primer.py

    # Just list models you can access
    python bedrock_primer.py --list-only
"""

import argparse
import json
import os
import time

import anthropic
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv


load_dotenv()


# Bedrock configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Cross-region inference profile — required for Claude Sonnet 4.6 on-demand.
# The plain region-pinned ID `anthropic.claude-sonnet-4-6` will raise
# `ValidationException: Invocation of model ID ... with on-demand throughput
# isn't supported.` AWS requires newer Claude models to route through an
# inference profile (us./eu./apac. prefix), which gives us 2-3x higher
# rate limits transparently at no cost difference.
BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-6"

# Direct Anthropic API model name (same model, different access path)
ANTHROPIC_MODEL_ID = "claude-sonnet-4-6"

# Test prompt — small, predictable, easy to compare answers
TEST_PROMPT = "In exactly two sentences, explain what a vector database is."

# Claude Sonnet 4.6 pricing (as of 2026-06; update if Anthropic changes prices)
# These are per-million-token rates. Bedrock pricing matches direct API for Claude.
PRICE_PER_M_INPUT_TOKENS_USD = 3.00
PRICE_PER_M_OUTPUT_TOKENS_USD = 15.00


def list_accessible_claude_models(bedrock):
    """List Claude foundation models your account has access to.

    A model appearing here does NOT mean you have access — you may need to request
    access in the Bedrock console. But it confirms the model exists in your region.
    """
    print("\n=== Claude models visible in Bedrock ===")
    try:
        response = bedrock.list_foundation_models(byProvider="anthropic")
        for model in response.get("modelSummaries", []):
            mid = model["modelId"]
            name = model.get("modelName", "?")
            status = "TEXT" if "TEXT" in model.get("outputModalities", []) else "?"
            print(f"  {mid:<55s}  {name:<30s}  [{status}]")
    except ClientError as e:
        print(f"  ERROR listing models: {e.response['Error']['Code']} — {e.response['Error']['Message']}")
        print("  Check that your IAM policy includes bedrock:ListFoundationModels")


def list_cross_region_profiles(bedrock):
    """Show available cross-region inference profiles (the 'us.' / 'eu.' prefixed IDs)."""
    print("\n=== Cross-region inference profiles ===")
    try:
        response = bedrock.list_inference_profiles()
        for profile in response.get("inferenceProfileSummaries", []):
            pid = profile["inferenceProfileId"]
            name = profile.get("inferenceProfileName", "?")
            regions = [r["region"] for r in profile.get("models", [{}])[0].get("regions", [])] if profile.get("models") else []
            regions_str = ",".join(regions) if regions else "?"
            print(f"  {pid:<55s}  {name:<35s}  [{regions_str}]")
    except ClientError as e:
        print(f"  ERROR listing profiles: {e.response['Error']['Code']} — {e.response['Error']['Message']}")


def call_via_bedrock(prompt: str) -> dict:
    """Invoke Claude Sonnet through Bedrock and return timing + response + usage."""
    # bedrock-runtime is the client for actually invoking models (different from bedrock
    # which is the control-plane client used above for listing).
    runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    # Bedrock's Claude wrapper accepts the Anthropic Messages API request body verbatim,
    # but wrapped in Bedrock's invoke_model envelope. The body must be JSON-encoded bytes.
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",   # required by Bedrock
        "max_tokens": 256,
        "messages": [{"role": "user", "content": prompt}],
    }

    start = time.time()
    response = runtime.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(request_body).encode("utf-8"),
        contentType="application/json",
        accept="application/json",
    )
    elapsed_ms = int((time.time() - start) * 1000)

    # Response body is a streaming object — read it once
    body = json.loads(response["body"].read())

    return {
        "text": body["content"][0]["text"],
        "input_tokens": body["usage"]["input_tokens"],
        "output_tokens": body["usage"]["output_tokens"],
        "stop_reason": body.get("stop_reason"),
        "latency_ms": elapsed_ms,
        "raw_model_id": body.get("model", BEDROCK_MODEL_ID),
    }


def call_via_anthropic(prompt: str) -> dict:
    """Invoke Claude Sonnet through the direct Anthropic API for comparison."""
    # Same prompt, same model, different route — useful to confirm the answers match
    # and to compare end-to-end latency.
    client = anthropic.Anthropic()

    start = time.time()
    response = client.messages.create(
        model=ANTHROPIC_MODEL_ID,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed_ms = int((time.time() - start) * 1000)

    return {
        "text": response.content[0].text,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
        "latency_ms": elapsed_ms,
        "raw_model_id": response.model,
    }


def compute_cost_usd(input_tokens: int, output_tokens: int) -> float:
    """Compute USD cost for a single call given token counts."""
    return (
        input_tokens * PRICE_PER_M_INPUT_TOKENS_USD / 1_000_000
        + output_tokens * PRICE_PER_M_OUTPUT_TOKENS_USD / 1_000_000
    )


def print_side_by_side(bedrock_result: dict, anthropic_result: dict):
    """Print the two responses side-by-side for comparison."""
    print("\n=== Side-by-side comparison ===\n")
    print(f"{'Metric':<22} {'Bedrock':<28} {'Direct Anthropic':<28}")
    print("-" * 78)

    rows = [
        ("Model ID", bedrock_result["raw_model_id"][:26], anthropic_result["raw_model_id"][:26]),
        ("Input tokens", str(bedrock_result["input_tokens"]), str(anthropic_result["input_tokens"])),
        ("Output tokens", str(bedrock_result["output_tokens"]), str(anthropic_result["output_tokens"])),
        ("Stop reason", str(bedrock_result["stop_reason"]), str(anthropic_result["stop_reason"])),
        ("Latency (ms)", str(bedrock_result["latency_ms"]), str(anthropic_result["latency_ms"])),
        (
            "Cost (USD)",
            f"${compute_cost_usd(bedrock_result['input_tokens'], bedrock_result['output_tokens']):.6f}",
            f"${compute_cost_usd(anthropic_result['input_tokens'], anthropic_result['output_tokens']):.6f}",
        ),
    ]
    for metric, b_val, a_val in rows:
        print(f"{metric:<22} {b_val:<28} {a_val:<28}")

    print("\n--- Bedrock response ---")
    print(bedrock_result["text"])
    print("\n--- Direct Anthropic response ---")
    print(anthropic_result["text"])


def main():
    parser = argparse.ArgumentParser(description="AWS Bedrock primer for Claude")
    parser.add_argument("--list-only", action="store_true",
                        help="Just list accessible models and exit (no invocation)")
    args = parser.parse_args()

    # bedrock is the control-plane client (list/describe). bedrock-runtime is the
    # invocation client. Two separate clients with the same credentials.
    try:
        bedrock = boto3.client("bedrock", region_name=AWS_REGION)
    except NoCredentialsError:
        print("ERROR: AWS credentials not found.")
        print("Configure them via `aws configure` or set AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY.")
        return

    print(f"AWS region: {AWS_REGION}")
    print(f"Bedrock model ID: {BEDROCK_MODEL_ID}")

    # Step 1: list what we can see
    list_accessible_claude_models(bedrock)
    list_cross_region_profiles(bedrock)

    if args.list_only:
        return

    # Step 2: call via Bedrock
    print(f"\n[bedrock] invoking with prompt: '{TEST_PROMPT}'")
    try:
        bedrock_result = call_via_bedrock(TEST_PROMPT)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        print(f"\nERROR calling Bedrock: {code} — {msg}")
        if code == "AccessDeniedException":
            print("Likely cause: model access not yet granted. Visit:")
            print("  https://console.aws.amazon.com/bedrock → Model access → Request model access")
        return

    # Step 3: call via direct Anthropic for comparison
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n(Skipping direct-Anthropic comparison — ANTHROPIC_API_KEY not set)")
        print("\n=== Bedrock response only ===")
        print(bedrock_result["text"])
        print(f"\nLatency: {bedrock_result['latency_ms']} ms · "
              f"Tokens: {bedrock_result['input_tokens']} in / {bedrock_result['output_tokens']} out · "
              f"Cost: ${compute_cost_usd(bedrock_result['input_tokens'], bedrock_result['output_tokens']):.6f}")
        return

    print(f"[anthropic] invoking same prompt via direct API")
    anthropic_result = call_via_anthropic(TEST_PROMPT)

    # Step 4: print comparison
    print_side_by_side(bedrock_result, anthropic_result)


if __name__ == "__main__":
    main()
