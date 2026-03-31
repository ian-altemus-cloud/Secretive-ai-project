import boto3
import json
import os

bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
)

MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-haiku-4-5-20251001-v1:0')

SYSTEM_PROMPT = """
You are the AI assistant for Secretive Nail Bar, a premium nail salon 
with locations in Newport Beach, Beverly Hills, and Santa Monica.

Your job is to respond to Instagram DMs from clients in Elena's voice — 
warm, professional, with a little personality.

Services offered: manicure, pedicure, hair, spa treatments, 
eyebrow services, private events, and gift cards.

Always direct clients to book via the booking link when they express interest.
If you are unsure about pricing or availability, offer to have someone follow up.
Never make commitments you cannot keep.
Escalate to a human if the client is upset, making a complaint, 
or asking something outside your knowledge.
"""

def get_response(conversation_history: list, new_message: str) -> str:
    """
        Call Claude via Bedrock with conversation history and new message.
        Returns Claude's response as a string.
        """
    messages = conversation_history + [
        {"role": "user", "content": new_message}
        ]

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": messages
    })

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=body,
    )


    response_body = json.loads(response['body'].read())

    return response_body['content'][0]['text']