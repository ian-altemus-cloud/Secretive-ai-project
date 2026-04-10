import os
import json
import boto3
import hmac
import hashlib
import requests
import sys
sys.stdout.reconfigure(line_buffering=True)
from flask import Flask, request, jsonify

from metrics import track_dm_received, track_booking_link_sent, track_meta_error, start_metrics_server
from bedrock_client import get_response
from conversation_store import  get_conversation_history, save_message
from sheets_logger import log_conversation, get_conversations
from flask_cors import CORS
from auth_handler import auth_bp


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.register_blueprint(auth_bp)

# SQS client
sqs = boto3.client('sqs', region_name='us-east-1')
QUEUE_URL = os.environ.get('SQS_QUEUE_URL')
VERIFY_TOKEN = os.environ.get('META_VERIFY_TOKEN')
APP_SECRET = os.environ.get('META_APP_SECRET')
META_ACCESS_TOKEN = os.environ.get('META_ACCESS_TOKEN')
DASHBOARD_SECRET_ARN = os.environ.get('DASHBOARD_API_KEY_ARN')
META_API_URL = "https://graph.instagram.com/v21.0/me/messages"
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
kms = boto3.client('kms', region_name='us-east-1')
TENANT_TABLE = os.environ.get('TENANT_TABLE')

PROMPT_BUCKET = os.environ.get('PROMPT_BUCKET')
GENERIC_FALLBACK = "Hey! For the fastest help reach out to our team directly. We will get back to you shortly"

def get_client_config(instagram_account_id: str) -> dict:
    """
    Fetch client access token and system prompt.
    Primary: DynamoDB
    Secondary prompt fallback: S3
    Last resort: generic fallback message
    No account ID: returns None, caller handles exit
    """
    import base64

    if not instagram_account_id:
        return None

    table = dynamodb.Table(TENANT_TABLE)
    s3 = boto3.client('s3', region_name='us-east-1')

    access_token = None
    system_prompt = None

    # Primary — DynamoDB
    try:
        item = table.get_item(
            Key={'instagram_account_id': instagram_account_id}
        ).get('Item')

        if item:
            ciphertext = base64.b64decode(item['encrypted_token'])
            decrypted = kms.decrypt(
                CiphertextBlob=ciphertext,
                KeyId=os.environ.get('KMS_KEY_ARN')
            )
            access_token = decrypted['Plaintext'].decode()
            system_prompt = item.get('system_prompt')
            if system_prompt:
                print(f"Prompt loaded from DynamoDB for {instagram_account_id}", flush=True)

    except Exception as e:
        print(f"DynamoDB lookup failed for {instagram_account_id}: {e}", flush=True)

    # Secondary — S3
    if not system_prompt:
        try:
            obj = s3.get_object(Bucket=PROMPT_BUCKET, Key=f"prompts/{instagram_account_id}.txt")
            system_prompt = obj['Body'].read().decode('utf-8')
            print(f"Prompt loaded from S3 for {instagram_account_id}", flush=True)
        except Exception as e:
            print(f"S3 prompt fetch failed for {instagram_account_id}: {e}", flush=True)

    # Last resort
    if not system_prompt:
        print(f"CRITICAL: No prompt found for {instagram_account_id}, using generic fallback", flush=True)
        system_prompt = GENERIC_FALLBACK

    return {
        'access_token': access_token,
        'system_prompt': system_prompt
    }

def verify_signature(payload, signature):
    """Verify the request came from Meta using HMAC SHA256"""
    expected = 'sha256=' + hmac.new(
        APP_SECRET.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Meta webhook verification handshake"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return jsonify({'error': 'Verification failed'}), 403

@app.route('/webhook', methods=['POST'])
def receive_webhook():
    """Receive incoming Instagram DM events from Meta"""
    signature = request.headers.get('X-Hub-Signature-256', '')

    if not verify_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 403

    data = request.get_json()

    if data.get('object') != 'instagram':
        return jsonify({'status': 'ignored'}), 200

    for entry in data.get('entry', []):
        for messaging in entry.get('messaging', []):
            track_dm_received()
            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(messaging)
            )
    return jsonify({'status': 'ok'}), 200

def send_instagram_message(recipient_id: str, message_text: str, access_token: str) -> bool:
    """Send a message back to Instagram user via Meta Graph API"""

    try:
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text},
            "messaging_type": "RESPONSE"
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        response = requests.post(META_API_URL, json=payload, headers=headers)
        print(f"Meta API response: {response.status_code} {response.text}", flush=True)

        if response.status_code != 200:
            track_meta_error()
            return False
        return True

    except Exception as e:
        print(f"Error sending Instagram message: {e}", flush=True)
        track_meta_error()
        return False


def process_message(messaging: dict) -> None:
    """
    Process a single Instagram DM message.
    Called by the SQS consumer for each message pulled from the queue.
    """
    try:
        sender_id = messaging.get('sender', {}).get('id')
        message_text = messaging.get('message', {}).get('text', '')
        print(f"sender_id={sender_id}, message_text={message_text}", flush=True)

        if not sender_id or not message_text:
            print(f"Early return: sender_id={sender_id}, message_text={message_text}", flush=True)
            return

        print(f"Processing message from {sender_id}: {message_text}", flush=True)

        # Get conversation history from DynamoDB
        history = get_conversation_history(sender_id)

        # Save incoming user message
        save_message(sender_id, 'user', message_text)

        # Get client config — token and prompt
        recipient_id = messaging.get('recipient', {}).get('id')
        client_config = get_client_config(recipient_id)

        if not client_config:
            print(f"No recipient ID, skipping message", flush=True)
            return

        access_token = client_config['access_token'] or META_ACCESS_TOKEN
        system_prompt = client_config['system_prompt']

        # Get Claude's response
        ai_response = get_response(history, message_text, system_prompt)
        print(f"AI response: {ai_response}", flush=True)

        # Save Claude's response
        save_message(sender_id, 'assistant', ai_response)

        # Send response back to Instagram
        result = send_instagram_message(sender_id, ai_response, access_token)
        print(f"Send result: {result}", flush=True)

        # Check if booking link was mentioned
        booking_link_sent = 'booking' in ai_response.lower()
        if booking_link_sent:
            track_booking_link_sent()

        # Log to Google Sheets
        log_conversation(
            instagram_user_id=sender_id,
            source='instagram',
            intent='dm',
            user_message=message_text,
            assistant_response=ai_response,
            booking_link_sent=booking_link_sent
        )

    except Exception as e:
        import traceback
        print(f"Error processing message: {e}", flush=True)
        print(traceback.format_exc(), flush=True)

def run_sqs_consumer() -> None:
    """
    Continuously poll SQS queue and process messages.
    This runs as the main loop inside the Fargate container.
    """
    import time
    print("SQS consumer started. Polling for messages...")

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )

            messages = response.get('Messages', [])

            for msg in messages:
                print(f"SQS message received: {msg['Body'][:200]}", flush=True)
                raw = msg['Body']
                if raw.startswith('Action=SendMessage'):
                    from urllib.parse import parse_qs
                    parsed = parse_qs(raw)
                    body = json.loads(parsed['MessageBody'][0])
                    print(f"Parsed body: {body}", flush=True)
                else:
                    body = json.loads(raw)
                    print(f"Direct body: {body}", flush=True)

                try:
                    for entry in body.get('entry', []):
                        for messaging in entry.get('messaging', []):
                            process_message(messaging)
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=msg['ReceiptHandle']
                    )
                except ValueError as e:
                    # Configuration error — no client record or no prompt
                    # Retrying will not fix this, delete and log
                    print(f"Configuration error, deleting message: {e}", flush=True)
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=msg['ReceiptHandle']
                    )
                except Exception as e:
                    # Transient error — leave in queue for retry
                    print(f"Failed to process message, leaving in queue: {e}", flush=True)

        except Exception as e:
            print(f"SQS consumer error: {e}")
            time.sleep(5)

def get_dashboard_api_key() -> str:
    secret = boto3.client('secretsmanager', region_name='us-east-1').get_secret_value(
        SecretId=DASHBOARD_SECRET_ARN
    )
    return secret['SecretString']

@app.route('/api/conversations', methods=['GET'])
def conversations_endpoint():
    auth = request.headers.get('X-API-Key', '')
    try:
        expected = get_dashboard_api_key()
    except Exception as e:
        print(f"Error fetching dashboard key: {e}", flush=True)
        return jsonify({'error': 'Server error'}), 500

    if not hmac.compare_digest(auth, expected):
        return jsonify({'error': 'Unauthorized'}), 403

    data = get_conversations()
    return jsonify(data), 200

if __name__ == '__main__':
    from threading import Thread

    consumer_thread = Thread(target=run_sqs_consumer)
    consumer_thread.daemon = True
    consumer_thread.start()

    # Start Prometheus metrics server on port 8000
    metrics_thread = Thread(target=start_metrics_server, args=(8000,))
    metrics_thread.daemon = True
    metrics_thread.start()

    #Start Flask webhook receiver
    app.run(host='0.0.0.0', port=80)