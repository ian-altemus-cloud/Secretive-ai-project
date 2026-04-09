import os
import time
import base64
import secrets
import boto3
import jwt
import requests
from flask import Blueprint, redirect, request
from urllib.parse import urlencode

auth_bp = Blueprint('auth', __name__)

# Clients
kms = boto3.client('kms', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
secretsmanager = boto3.client('secretsmanager', region_name='us-east-1')

# Env vars
META_APP_ID = os.environ.get('META_APP_ID')
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
        'scope':         'instagram_business_manage_messages',
        'response_type': 'code',
        'state':         state,
    }


    meta_url = f"https://www.instagram.com/oauth/authorize?{urlencode(params)}"
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

    # KMS encrypt token
    encrypted = kms.encrypt(
        KeyId=KMS_KEY_ARN,
        Plaintext=long_token.encode()
    )
    encrypted_b64 = base64.b64encode(encrypted['CiphertextBlob']).decode()

    # Store in DynamoDB
    table = dynamodb.Table(TENANT_TABLE)
    table.put_item(Item={
        'instagram_account_id': instagram_account_id,
        'encrypted_token':      encrypted_b64,
        'token_expiry':         int(time.time()) + (60 * 86400),
        'webhook_subscribed':   False,
        'status':               'active',
        'onboarded_at':         time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    })

    print(f"Tenant {instagram_account_id} onboarded successfully", flush=True)

    return redirect('https://silverlinkai.com/#connected')
