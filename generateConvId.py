import json
import uuid
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
user_table = dynamodb.Table("user-table")
conversation_table = dynamodb.Table("conversation-table")  # New table

def lambda_handler(event, context):
    try:
        # Handle API Gateway & direct Lambda test events
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("userId")
        conversation_id = body.get("conversationId")

        if not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "userId is required"
                })
            }

        # --------------------------------------------------
        # CASE 1: Existing conversation (skip DB update)
        # --------------------------------------------------
        if conversation_id:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Existing conversation",
                    "conversationId": conversation_id,
                    "isNew": False
                })
            }

        # --------------------------------------------------
        # CASE 2: Create new conversation
        # --------------------------------------------------
        new_conversation_id = str(uuid.uuid4())

        # 1️⃣ Append conversationId to user's conversationIds
        user_table.update_item(
            Key={"userId": user_id},
            UpdateExpression="""
                SET conversationIds = list_append(
                    if_not_exists(conversationIds, :empty),
                    :new_conv
                )
            """,
            ExpressionAttributeValues={
                ":new_conv": [new_conversation_id],
                ":empty": []
            },
            ConditionExpression="attribute_exists(userId)"
        )
        # obtain the timestamp
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).isoformat()

        # 2️⃣ Create new conversation record in conversation_data table
        conversation_table.put_item(
            Item={
                "conversationId": new_conversation_id,
                "history": [],
                "lastUpdated": ts
            }
        )

        return {
            "statusCode": 201,
            "body": json.dumps({
                "message": "New conversation created",
                "conversationId": new_conversation_id,
                "isNew": True
            })
        }

    except ClientError as e:
        # User not found
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "message": "User not found"
                })
            }

        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "DynamoDB error",
                "error": str(e)
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal server error",
                "error": str(e)
            })
        }