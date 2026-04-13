import boto3
import json
import os
import anthropic

bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
)

BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-haiku-4-5-20251001-v1:0')
ANTHROPIC_MODEL_ID = 'claude-haiku-4-5-20251001'
AI_PROVIDER = os.environ.get('AI_PROVIDER', 'anthropic')


def _call_anthropic(conversation_history: list, new_message: str, system_prompt: str) -> str:
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY env var not set")

    client = anthropic.Anthropic(api_key=api_key)

    messages = conversation_history + [
        {"role": "user", "content": new_message}
    ]

    print(f"System prompt length: {len(system_prompt)}", flush=True)
    print(f"System prompt preview: {system_prompt[:100]}", flush=True)

    response = client.messages.create(
        model=ANTHROPIC_MODEL_ID,
        max_tokens=1024,
        system=system_prompt,
        messages=messages
    )

    return response.content[0].text


def _call_bedrock(conversation_history: list, new_message: str, system_prompt: str) -> str:
    messages = conversation_history + [
        {"role": "user", "content": new_message}
    ]

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": messages
    })

    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=body
    )

    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']


def get_response(conversation_history: list, new_message: str, system_prompt: str) -> str:
    """
    Call AI provider with conversation history, new message, and system prompt.
    Provider selected by AI_PROVIDER env var: 'anthropic' or 'bedrock'.
    Returns response as a string.
    """
    if AI_PROVIDER == 'bedrock':
        return _call_bedrock(conversation_history, new_message, system_prompt)
    else:
        return _call_anthropic(conversation_history, new_message, system_prompt)