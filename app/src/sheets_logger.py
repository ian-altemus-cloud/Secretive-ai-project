import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import boto3

SPREADSHEET_ID = os.environ.get('GOOGLE_SPREADSHEET_ID')
SHEET_NAME = os.environ.get('GOOGLE_SHEET_NAME', 'Conversations')
SECRETS_ARN = os.environ.get('GOOGLE_SHEETS_SECRET_ARN')


def get_sheets_service():
    """Get authenticated Google Sheets service using credentials from Secrets Manager"""
    secrets_client = boto3.client('secretsmanager', region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
    secret = secrets_client.get_secret_value(SecretId=SECRETS_ARN)
    credentials_json = json.loads(secret['SecretString'])

    credentials = service_account.Credentials.from_service_account_info(
        credentials_json,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

    return build('sheets', 'v4', credentials=credentials)


def log_conversation(instagram_user_id: str, source: str, intent: str,
                     user_message: str, assistant_response: str,
                     booking_link_sent: bool) -> None:
    """
    Append a conversation row to Google Sheets.
    """
    try:
        from datetime import datetime
        service = get_sheets_service()

        row = [
            datetime.utcnow().isoformat(),
            instagram_user_id,
            source,
            intent,
            user_message,
            assistant_response,
            'Yes' if booking_link_sent else 'No',
        ]

        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A:G',
            valueInputOption='RAW',
            body={'values': [row]}
        ).execute()

    except Exception as e:
        print(f"Error logging to Google Sheets: {e}")

def get_conversations() -> list:
    """
    Read all conversations from Google Sheets.
    Returns a list of dicts matching the column headers.
    """
    try:
        service = et.sheets_service()
        results = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A:G'
        ).execute()

        rows = result.get('values', [])
        if not rows:
            return []

        headers = rows[0]
        conversations = []
        for row in rows[1:]:
            padded = row + [''] * (len(headers) - len(row))
            conversations.append(dict(zip(headers, padded)))

            return conversations
    except Exception as e:
        print(f"Error logging to Google Sheets: {e}", flush=True)
        return []
