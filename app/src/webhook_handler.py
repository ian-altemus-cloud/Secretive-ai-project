import os
import json
import boto3
import hmac
import hashlib
from flask import Flask, request, jsonify
from metrics import track_dm_received

app = Flask(__name__)

# SQS client
sqs = boto3.client('sqs',region_name='us-east-1')
QUEUE_URL = os.environ.get('SQS_QUEUE_URL')
VERIFY_TOKEN = os.environ.get('META_VERIFY_TOKEN')
APP_SECRET = os.environ.get('META_APP_SECRET')

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
            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(messaging)
            )
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)