import json
import boto3

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Table names
USERS_TABLE = "user-table"
CONVERSATIONS_TABLE = "conversation-table"

def lambda_handler(event, context):
    """
    Lambda function to fetch conversation history for a given userId.
    
    Expected input: {"userId": "<user-id>"}
    """
    
    # 1. Get userId from event
    if "body" in event:
        body = event.body
    else:
        body = event
    
    user_id = body.get('userId')
    print("userId",user_id)
    if not user_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "userId is required"})
        }
    
    # 2. Fetch the user's conversation IDs from table 1
    users_table = dynamodb.Table(USERS_TABLE)
    try:
        user_response = users_table.get_item(Key={'userId': user_id})
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Error fetching user: {str(e)}"})
        }
    
    if 'Item' not in user_response:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "User not found"})
        }
    
    conversation_ids_raw = user_response['Item'].get('conversationIds', [])
    print("conversation_ids_raw",conversation_ids_raw)
    
    # Extract string conversation IDs from DynamoDB list of maps
    # conversation_ids = [c['S'] for c in conversation_ids_raw if 'S' in c]
    conversation_ids = conversation_ids_raw
    
    if not conversation_ids:
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No conversations found", "conversations": []})
        }
    
    # 3. Fetch all conversations using batch_get_item
    dynamodb_client = boto3.client('dynamodb')
    
    keys = [{'conversationId': {'S': conv_id}} for conv_id in conversation_ids]
    
    try:
        response = dynamodb_client.batch_get_item(
            RequestItems={
                CONVERSATIONS_TABLE: {
                    'Keys': keys
                }
            }
        )
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Error fetching conversations: {str(e)}"})
        }
    
    conversations_data = []
    
    for item in response['Responses'].get(CONVERSATIONS_TABLE, []):
        conv_id = item['conversationId']['S']
        history = item.get('history', [])
        
        # ✅ Read top-level lastUpdated timestamp
        last_updated = item.get('lastUpdated', {}).get('S', '')

        # Convert DynamoDB list/map format to normal JSON if needed
        print("history", history)
        # formatted_history = []
        # for h in history:
        #     if 'M' in h:
        #         formatted_history.append({
        #             'user': h['M'].get('user', {}).get('S', ''),
        #             'assistant': h['M'].get('assistant', {}).get('S', '')
        #         })
        # print("formatted_history",formatted_history)
        


        # Convert DynamoDB list/map format to normal JSON
        formatted_history = []

        # DynamoDB list format is under 'L'
        for h in history.get('L', []):
            if 'M' in h:
                formatted_history.append({
                    'user': h['M'].get('user', {}).get('S', ''),
                    'assistant': h['M'].get('assistant', {}).get('S', ''), 
                })
        print("formatted_history", formatted_history)

        conversations_data.append({
            "conversationId": conv_id,
            "lastUpdated": last_updated,   # used for sorting
            "history": formatted_history
        })
    
    conversations_data.sort(
        key=lambda c: c.get("lastUpdated", "")
    )

    # 4. Return structured response
    return {
        "statusCode": 200,
        "body": json.dumps({
            "userId": user_id,
            "conversations": conversations_data
        }, default=str)
    }