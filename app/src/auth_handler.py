import os
import time
import base64
import secrets
import boto3
import jwt
import requests
from flask import Blueprint, redirect, request,jsonify
from urllib.parse import urlencode

auth_bp = Blueprint('auth', __name__)

# Clients
kms = boto3.client('kms', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Env vars
META_APP_ID = os.environ.get('INSTAGRAM_APP_ID')
OAUTH_REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI')
KMS_KEY_ARN = os.environ.get('KMS_KEY_ARN')
TENANT_TABLE = os.environ.get('TENANT_TABLE')

def get_jwt_secret() -> str:
    return os.environ.get('JWT_SECRET_KEY')

def get_meta_app_secret() -> str:
    return os.environ.get('META_APP_SECRET')


@auth_bp.route('/auth/login')
def login():
    jwt_secret = get_jwt_secret()
    state = jwt.encode(
        {
            'nonce': secrets.token_urlsafe(32),
            'exp': int(time.time()) + 600
        },
        jwt_secret,
        algorithm='HS256'
    )

    params = {
        'client_id':     META_APP_ID,
        'redirect_uri':  OAUTH_REDIRECT_URI,
        'scope':         'instagram_business_basic,instagram_business_manage_messages',
        'response_type': 'code',
        'state':         state,
    }


    meta_url = f"https://api.instagram.com/oauth/authorize?{urlencode(params)}"
    print(f"OAuth login initiated, redirecting to Meta", flush=True)
    return redirect(meta_url)

@auth_bp.route('/auth/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')

    if not code or not state:
        print("Missing code or state in callback", flush=True)
        return "Invalid request", 400

    # Verify JWT state
    try:
        jwt_secret = get_jwt_secret()
        jwt.decode(state, jwt_secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        print("OAuth state expired", flush=True)
        return "Session expired. Please try again.", 400
    except jwt.InvalidTokenError:
        print("Invalid OAuth state", flush=True)
        return "Invalid request.", 400

    app_secret = get_meta_app_secret()

    # Exchange code for short-lived token
    token_resp = requests.post(
        'https://api.instagram.com/oauth/access_token',
        data={
            'client_id':     META_APP_ID,
            'client_secret': app_secret,
            'grant_type':    'authorization_code',
            'redirect_uri':  OAUTH_REDIRECT_URI,
            'code':          code,
        }
    ).json()

    if 'error' in token_resp:
        print(f"Token exchange error: {token_resp}", flush=True)
        return "Authentication failed.", 400

    short_token = token_resp['access_token']
    instagram_account_id = str(token_resp['user_id'])

    # Exchange for long-lived token
    ll_resp = requests.get(
        'https://graph.instagram.com/access_token',
        params={
            'grant_type':    'ig_exchange_token',
            'client_secret': app_secret,
            'access_token':  short_token,
        }
    ).json()

    if 'error' in ll_resp:
        print(f"Long-lived token exchange error: {ll_resp}", flush=True)
        return "Authentication failed.", 400

    long_token = ll_resp['access_token']

    # Get the correct Instagram account ID that matches webhook events
    me_resp = requests.get(
        'https://graph.instagram.com/v21.0/me',
        params={
            'fields': 'user_id,username',
            'access_token': long_token,
        }
    ).json()

    instagram_account_id = str(me_resp.get('user_id') or instagram_account_id)
    print(f"Instagram account ID for webhooks: {instagram_account_id}", flush=True)


    # KMS encrypt token
    encrypted = kms.encrypt(
        KeyId=KMS_KEY_ARN,
        Plaintext=long_token.encode()
    )
    encrypted_b64 = base64.b64encode(encrypted['CiphertextBlob']).decode()

    # Store in DynamoDB
    table = dynamodb.Table(TENANT_TABLE)
    table.update_item(
        Key={'instagram_account_id': instagram_account_id},
        UpdateExpression='''SET
        encrypted_token = :t,
        token_expiry = :e,
        webhook_subscribed = :w,
        #s = :s,
        onboarded_at = :o,
        username = :u
        ''',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={
            ':t': encrypted_b64,
            ':e': int(time.time()) + (60 * 86400),
            ':w': False,
            ':s': 'active',
            ':o': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            ':u': me_resp.get('username', '')
        }
    )

    # Subscribe to webhook
    subscribe_resp = requests.post(
        f"https://graph.instagram.com/v21.0/{instagram_account_id}/subscribed_apps",
        params={
            'subscribed_fields': 'messages',
            'access_token': long_token,
        }
    ).json()

    if subscribe_resp.get('success'):
        table.update_item(
            Key={'instagram_account_id': instagram_account_id},
            UpdateExpression='SET webhook_subscribed = :t',
            ExpressionAttributeValues={':t': True}
        )
        print(f"Webhook subscribed for {instagram_account_id}", flush=True)
    else:
        print(f"Webhook subscription failed for {instagram_account_id}: {subscribe_resp}", flush=True)

    print(f"Client {instagram_account_id} onboarded successfully", flush=True)
    return redirect('https://silverlinkai.com/#connected')




@auth_bp.route('/auth/deauthorize', methods=['POST'])
def deauthorize():
    data = request.get_json()
    instagram_account_id = str(data.get('user_id', ''))

    if instagram_account_id:
        table = dynamodb.Table(TENANT_TABLE)
        table.update_item(
            Key={'instagram_account_id': instagram_account_id},
            UpdateExpression='SET #s = :s',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'revoked'}
        )
        print(f"Client {instagram_account_id} deauthorized", flush=True)

    return jsonify({'status': 'ok'}), 200