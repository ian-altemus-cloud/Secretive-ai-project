import os
import json
import boto3
import requests
from conversation_store import get_conversation_history, save_message
from sheets_logger import log_conversation

secretsmanager = boto3.client('secretsmanager', region_name='us-east-1')

DYNAMODB_TABLE_NAME = os.environ.get['DYNAMODB_TABLE_NAME']
META_API_TOKEN_ARN = os.environ.get['META_API_TOKEN_ARN']
ANTHROPIC_API_KEY_ARN = os.environ.get('ANTHROPIC_API_KEY_ARN')
GOOGLE_SHEETS_SECRET_ARN = os.environ.get('GOOGLE_SHEETS_SECRET_ARN')
META_API_URL = "https://graph.facebook.com/v18.0/me/messages"

FOLLOWUP_SYSTEM_PROMPT = """
You are the AI assistant for Secretive Nail Bar, a premium nail salon
with locations in Newport Beach, Beverly Hills, and Santa Monica.

A client reached out earlier but hasn't responded. Send one warm,
natural follow-up message in Elena's voice. Keep it brief, friendly,
and non-pushy. Reference the conversation context if relevant.
Never mention that you are an AI. Never say "following up" directly.
"""

def get_secret(secret_arn: str) -> str:
    response = secretsmanager.get_secret_value(SecretArn=secret_arn)
    return response['SecretString']


def get_anthropic_response(history: list, system_prompt: str) -> str:
    import anthropic
    api_key = get_secret(ANTHROPIC_API_KEY_ARN)
    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=system_prompt,
        messages=history
    )
    return response.content[0].text


def send_instagram_message(recipient_id: str, message_text: str) -> bool:
    try:
        meta_token = get_secret(META_API_TOKEN_ARN)
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        headers = {
            "Authorization": f"Bearer {meta_token}",
            "Content-Type": "application/json"
        }
        response = requests.post(META_API_URL, json=payload, headers=headers)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending follow-up message: {e}", flush=True)
        return False

def lambda_handler(event, context):
    try:
        instagram_user_id = event.get('instagram_user_id')
        if not instagram_user_id:
            print("No instagram_user_id in event payload.", flush=True)
            return {'statusCode': 400, 'body': 'Missing instagram_user_id'}

        history = get_conversation_history(instagram_user_id)

        if not history:
            print(f"No conversation history for {instagram_user_id}", flush=True)
            return {'statusCode': 200, 'body': 'No history found'}

        ai_response = get_anthropic_response(history, FOLLOWUP_SYSTEM_PROMPT)

        save_message(instagram_user_id, 'assistant', ai_response)

        success = send_instagram_message(instagram_user_id, ai_response)

        log_conversation(
            instagram_user_id=instagram_user_id,
            source='instagram',
            intent='followup',
            user_message='',
            assistance_message=ai_response,
            booking_link_sent='booking' in ai_response.lower()
        )

        print(f"Follow-up sent to {instagram_user_id}: {success}", flush=True)
        return {'statusCode': 200, 'body': 'Follow-up sent'}

    except Exception as e:
        print(f"Lambda error: {e}", flush=True)
        return {'statusCode': 500, 'body': str(e)}