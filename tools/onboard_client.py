#!/usr/bin/env python3
"""
SilverLink AI — Client Onboarding Tool
Usage: python tools/onboard_client.py
"""

import boto3
import base64
import os
import sys
from datetime import datetime, timezone

# Config
REGION = "us-east-1"
KMS_KEY_ALIAS = "alias/secretive-nail-bar-dev-tenant-tokens"
TENANT_TABLE = "secretive-nail-bar-dev-tenant-tokens"

dynamodb = boto3.resource('dynamodb', region_name=REGION)
kms = boto3.client('kms', region_name=REGION)
table = dynamodb.Table(TENANT_TABLE)

def encrypt_token(token: str) -> str:
    """KMS encrypt the access token and return base64 encoded ciphertext."""
    response = kms.encrypt(
        KeyId=KMS_KEY_ALIAS,
        Plaintext=token.encode('utf-8')
    )
    return base64.b64encode(response['CiphertextBlob']).decode('utf-8')

def load_prompt(prompt_path: str) -> str:
    """Load prompt from file."""
    with open(prompt_path, 'r') as f:
        return f.read().strip()

def check_existing(instagram_account_id: str) -> bool:
    """Check if a client record already exists."""
    response = table.get_item(
        Key={'instagram_account_id': instagram_account_id}
    )
    return 'Item' in response


def onboard_client(
    instagram_account_id: str,
    business_name: str,
    access_token: str,
    prompt_path: str,
    prompt_version: str
) -> None:
    """Write client record to DynamoDB."""

    # Check for existing record
    if check_existing(instagram_account_id):
        confirm = input(f"\n⚠️  Record already exists for {instagram_account_id}. Overwrite? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    # Encrypt token
    print(f"\nEncrypting token for {business_name}...")
    encrypted_token = encrypt_token(access_token)
    print("✓ Token encrypted")

    # Load prompt
    print(f"Loading prompt from {prompt_path}...")
    system_prompt = load_prompt(prompt_path)
    print(f"✓ Prompt loaded ({len(system_prompt)} characters)")

    # Write to DynamoDB
    print(f"Writing client record to DynamoDB...")
    table.update_item(
        Key={'instagram_account_id': instagram_account_id},
        UpdateExpression='SET business_name = :b, system_prompt = :p, prompt_version = :v, updated_at = :u',
        ExpressionAttributeValues={
            ':b': business_name,
            ':p': system_prompt,
            ':v': prompt_version,
            ':u': datetime.now(timezone.utc).isoformat(),
        }
    )

    print(f"✓ Client record written")

    # Verify
    item = table.get_item(
        Key={'instagram_account_id': instagram_account_id}
    ).get('Item')

    if not item:
        print("\n❌ Verification failed — record not found after write.")
        sys.exit(1)

    print(f"\n✅ {business_name} onboarded successfully.")
    print(f"   Instagram Account ID : {instagram_account_id}")
    print(f"   Prompt version       : {prompt_version}")
    print(f"   Status               : {item['status']}")
    print(f"   Updated at           : {item['updated_at']}")


def onboard_client(
    instagram_account_id: str,
    business_name: str,
    access_token: str,
    prompt_path: str,
    prompt_version: str
) -> None:
    """Write client record to DynamoDB."""

    # Check for existing record
    if check_existing(instagram_account_id):
        confirm = input(f"\n⚠️  Record already exists for {instagram_account_id}. Overwrite? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    # Encrypt token
    print(f"\nEncrypting token for {business_name}...")
    encrypted_token = encrypt_token(access_token)
    print("✓ Token encrypted")

    # Load prompt
    print(f"Loading prompt from {prompt_path}...")
    system_prompt = load_prompt(prompt_path)
    print(f"✓ Prompt loaded ({len(system_prompt)} characters)")

    # Write to DynamoDB
    print(f"Writing client record to DynamoDB...")
    table.put_item(
        Item={
            'instagram_account_id': instagram_account_id,
            'business_name': business_name,
            'encrypted_token': encrypted_token,
            'system_prompt': system_prompt,
            'prompt_version': prompt_version,
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'status': 'active',
            'webhook_subscribed': True
        }
    )
    print(f"✓ Client record written")

    # Verify
    item = table.get_item(
        Key={'instagram_account_id': instagram_account_id}
    ).get('Item')

    if not item:
        print("\n❌ Verification failed — record not found after write.")
        sys.exit(1)

    print(f"\n✅ {business_name} onboarded successfully.")
    print(f"   Instagram Account ID : {instagram_account_id}")
    print(f"   Prompt version       : {prompt_version}")
    print(f"   Status               : {item['status']}")
    print(f"   Updated at           : {item['updated_at']}")

def main():
    print("=" * 50)
    print("  SilverLink AI — Client Onboarding")
    print("=" * 50)

    instagram_account_id = input("\nInstagram Account ID: ").strip()
    if not instagram_account_id:
        print("Error: Instagram Account ID is required.")
        sys.exit(1)

    business_name = input("Business Name: ").strip()
    if not business_name:
        print("Error: Business name is required.")
        sys.exit(1)

    access_token = input("Meta Access Token: ").strip()
    if not access_token:
        print("Error: Access token is required.")
        sys.exit(1)

    prompt_path = input("Prompt file path: ").strip()
    if not os.path.exists(prompt_path):
        print(f"Error: Prompt file not found at {prompt_path}")
        sys.exit(1)

    prompt_version = input("Prompt version (default: 1.0): ").strip() or "1.0"

    print(f"\nReview:")
    print(f"  Instagram Account ID : {instagram_account_id}")
    print(f"  Business Name        : {business_name}")
    print(f"  Prompt file          : {prompt_path}")
    print(f"  Prompt version       : {prompt_version}")

    confirm = input("\nProceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborted.")
        sys.exit(0)

    onboard_client(
        instagram_account_id=instagram_account_id,
        business_name=business_name,
        access_token=access_token,
        prompt_path=prompt_path,
        prompt_version=prompt_version
    )


if __name__ == '__main__':
    main()