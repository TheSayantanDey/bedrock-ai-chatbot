import json
import uuid
import time
import boto3
import hashlib
import os
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("user-table")

DEFAULT_CONVERSATION_TOKENS = 5  # Fixed starting value


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000
    )
    return f"{salt.hex()}:{pwd_hash.hex()}"


def lambda_handler(event, context):
    try:
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        name = body.get("name")
        email = body.get("email")
        password = body.get("password")

        if not name or not email or not password:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "name, email and password are required"
                })
            }

        token = str(uuid.uuid4())
        token_expires_at = int(time.time()) + (24 * 60 * 60)

        hashed_password = hash_password(password)

        user_item = {
            # ✅ Email is now Partition Key
            "email": email,
            "name": name,
            "password": hashed_password,
            "conversationIds": [],
            "remainingConversationTokens": DEFAULT_CONVERSATION_TOKENS,
            "token": token,
            "tokenExpiresAt": token_expires_at
        }

        # Prevent duplicate email registration
        table.put_item(
            Item=user_item,
            ConditionExpression="attribute_not_exists(email)"
        )

        response_user = user_item.copy()
        response_user.pop("password")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Login successful",
                "user": response_user
            })
        }

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {
                "statusCode": 409,
                "body": json.dumps({
                    "message": "Email already registered"
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