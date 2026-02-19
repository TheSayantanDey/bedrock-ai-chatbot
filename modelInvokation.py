import boto3
import json

# Clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('conversation-table')

def lambda_handler(event, context):

    try:
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
    except (TypeError, json.JSONDecodeError):
        return {'statusCode': 400, 'body': json.dumps('Invalid JSON')}


    user_message = body.get('message', '')
    #conversation_id = body.get('conversationId', '')  # required
    conversation_id = body.get('conversationId', '100')  # required

    # 1. Handle preflight (OPTIONS) request for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps('Preflight OK')
        }
    # Fetch conversation history from DynamoDB
    # conversation_id = '100'
    try:
        db_response = table.get_item(
            Key={'conversationId': conversation_id}
        )
        db_history = db_response.get('Item', {}).get('history', [])
    except Exception as e:
        print(f"Error fetching history from DynamoDB: {str(e)}")
        db_history = []

    # 2. Parse incoming JSON safely
    
    history = db_history
    #user_id = body.get('userId')  # optional, not stored unless you want it

    if not conversation_id:
        return {
            'statusCode': 400,
            'body': json.dumps('conversation_id is required')
        }

    # 3. Construct Messages array for Nova
    messages = []
    for turn in history:
        messages.append({"role": "user", "content": [{"text": turn['user']}]})
        messages.append({"role": "assistant", "content": [{"text": turn['assistant']}]})

    messages.append({"role": "user", "content": [{"text": user_message}]})

    # 4. Create payload for Nova Micro
    request_body = {
        "messages": messages,
        "inferenceConfig": {
            "maxTokens": 300,
            "temperature": 0.7,
            "topP": 0.9,
            "stopSequences": []
        }
    }

    # 5. Call Nova Micro model
    try:
        response = bedrock.invoke_model(
            modelId='amazon.nova-micro-v1:0',
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )

        result = json.loads(response['body'].read())
        reply = result['output']['message']['content'][0]['text']

    except Exception as e:
        print(f"Error calling Bedrock: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to generate response from model'})
        }

    # 6. Save conversation turn to DynamoDB
    try:
        table.update_item(
            Key={'conversationId': conversation_id},
            UpdateExpression="""
                SET history = list_append(
                    if_not_exists(history, :empty_list),
                    :new_turn
                )
            """,
            ExpressionAttributeValues={
                ':empty_list': [],
                ':new_turn': [{
                    'user': user_message,
                    'assistant': reply
                }]
            }
        )
    except Exception as e:
        print(f"Error saving to DynamoDB: {str(e)}")

    # 7. Return response
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({'response': reply})
    }