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


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
# SQS client
sqs = boto3.client('sqs',region_name='us-east-1')
QUEUE_URL = os.environ.get('SQS_QUEUE_URL')
VERIFY_TOKEN = os.environ.get('META_VERIFY_TOKEN')
APP_SECRET = os.environ.get('META_APP_SECRET')
META_ACCESS_TOKEN = os.environ.get('META_ACCESS_TOKEN')
DASHBOARD_SECRET_ARN = os.environ.get('DASHBOARD_API_KEY_ARN')
META_API_URL = "https://graph.facebook.com/v18.0/me/messages"

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


def send_instagram_message(recipient_id: str, message_text: str) -> bool:
    """Send a message back to Instagram user via Meta Graph API"""
    try:
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        headers = {
            "Authorization": f"Bearer {META_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(META_API_URL, json=payload, headers=headers)

        if response.status_code != 200:
            track_meta_error()
            return False
        return True

    except Exception as e:
        print(f"Error sending Instagram message: {e}")
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

        if not sender_id or not message_text:
            return

        # Get conversation history from DynamoDB
        history = get_conversation_history(sender_id)

        # Save incoming user message
        save_message(sender_id, 'user', message_text)

        # Get Claude's response via Bedrock
        ai_response = get_response(history, message_text)

        # Save Claude's response
        save_message(sender_id, 'assistant', ai_response)

        # Send response back to Instagram
        send_instagram_message(sender_id, ai_response)

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
        print(f"Error processing message: {e}")

def manage_followup_schedule(instagram_user_id: str, cancel: bool = False) -> None:
    import boto3
    from datetime import datetime, timedelta
    import pytz

    scheduler = boto3.client('scheduler', region_name='us-east-1')
    schedule_name = f"follow-up-{instagram_user_id}"
    lambda_arn = os.environ.get('FOLLOWUP_LAMBDA_ARN')
    scheduler_role_arn = os.environ.get('SCHEDULER_ROLE_ARN')

    print(f"manage_followup_schedule called: user={instagram_user_id}, cancel={cancel}", flush=True)
    print(f"lambda_arn={lambda_arn}, scheduler_role_arn={scheduler_role_arn}", flush=True)

    try:
        scheduler.delete_schedule(Name=schedule_name, GroupName='default')
        print(f"deleted existing schedule for {instagram_user_id}", flush=True)
    except scheduler.exceptions.ResourceNotFoundException:
        pass

    if cancel:
        print(f"Cancel=True, skipping schedule creation for {instagram_user_id}", flush=True)
        return

    pst = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pst)
    target = now + timedelta(hours=24)

    delivery = target.replace(hour=10, minute=30, second=0, microsecond=0)
    if delivery < target:
        delivery += timedelta(days=1)

    schedule_expression = f"at({delivery.strftime('%Y-%m-%dT%H:%M:%S')})"
    print(f"Creating schedule: {schedule_expression} for {instagram_user_id}", flush=True)

    try:

        scheduler.create_schedule(
            Name=schedule_name,
            GroupName='default',
            ScheduleExpression=schedule_expression,
            ScheduleExpressionTimezone='America/Los_Angeles',
            FlexibleTimeWindow={'Mode': 'OFF'},
            Target={
                'Arn': lambda_arn,
                'RoleArn': scheduler_role_arn,
                'Input': json.dumps({'instagram_user_id': instagram_user_id})
            }
        )
        print(f"Follow_up scheduled for {instagram_user_id} at {delivery}", flush=True)
    except Exception as e:
        print(f"Error creating schedule for {instagram_user_id}: {e}", flush=True)

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
                body = json.loads(msg['Body'])

                try:
                    process_message(body)
                    sender_id = body.get('sender', {}).get('id')
                    if sender_id:
                        booking_detected = 'booking' in str(body).lower()
                        manage_followup_schedule(sender_id, cancel=booking_detected)
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=msg['ReceiptHandle']
                    )
                except Exception as e:
                    print(f"Failed to process message, leaving in queue: {e}")

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