import boto3
import json
import os

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
)

TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME')
table = dynamodb.Table(TABLE_NAME)

def get_conversation_history(instagram_user_id: str) -> list:
    """
    Retrieve conversation history for a user from DynamoDB.
    Returns a list of message dicts or empty list if new user.
    """
    try:
        response = table.get_item(
            Key={'instagram_user_id': instagram_user_id}
        )
        item = response.get('Item')
        if not item:
            return []
        return item.get('messages', [])
    except Exception as e:
        print(f"Error getting conversation history: {e}")
        return []



def save_message(instagram_user_id: str, role: str, content: str) -> None:
    """
    Save a single message to the conversation history in DynamoDB.
    Role is either 'user' or 'assistant'.
    """
    try:
        history = get_conversation_history(instagram_user_id)
        history.append({'role': role, 'content': content})

        table.put_item(
            Item={
                'instagram_user_id': instagram_user_id,
                'messages': history,
            }
        )
    except Exception as e:
        print(f"Error saving message: {e}")
