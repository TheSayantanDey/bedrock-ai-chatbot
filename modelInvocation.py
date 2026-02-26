import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")

USERS_TABLE = "user-table"
CONVERSATIONS_TABLE = "conversation-table"

users_table = dynamodb.Table(USERS_TABLE)
conversations_table = dynamodb.Table(CONVERSATIONS_TABLE)


def lambda_handler(event, context):
    try:
        # Handle API Gateway + direct Lambda invoke
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        email = body.get("email")

        if not email:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "email is required"})
            }

        # 1️⃣ Get user
        user_response = users_table.get_item(Key={"email": email})

        user = user_response.get("Item")

        if not user:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "User not found"})
            }

        conversation_ids = user.get("conversationIds", [])

        if not conversation_ids:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "email": email,
                    "conversations": []
                })
            }

        # 2️⃣ Fetch conversations (resource auto-deserializes)
        conversations_data = []

        for conv_id in conversation_ids:
            response = conversations_table.get_item(
                Key={"conversationId": conv_id}
            )

            conversation = response.get("Item")

            if not conversation:
                continue

            conversations_data.append({
                "conversationId": conversation["conversationId"],
                "lastUpdated": conversation.get("lastUpdated", ""),
                "history": conversation.get("history", [])
            })

        # Sort by lastUpdated (newest last)
        conversations_data.sort(
            key=lambda c: c.get("lastUpdated", ""),
            reverse = True
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "email": email,
                "conversations": conversations_data
            }, default=str)
        }

    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "DynamoDB error",
                "details": str(e)
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }