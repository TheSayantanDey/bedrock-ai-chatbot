import json
import uuid
import time
import boto3
import hashlib
import hmac
import os
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("user-table")

# Use env var or fallback (env var is strongly recommended)
SECRET_KEY = "sayantan-1q2w3e4r"


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
                "body": json.dumps({"message": "name, email and password are required"})
            }

        user_id = str(uuid.uuid4())
        token = str(uuid.uuid4())
        token_expires_at = int(time.time()) + (24 * 60 * 60)

        hashed_password = hash_password(password)

        user_item = {
            "userId": user_id,
            "name": name,
            "email": email,
            "password": hashed_password,
            "conversationIds": [],
            "token": token,
            "tokenExpiresAt": token_expires_at
        }

        table.put_item(
            Item=user_item,
            ConditionExpression="attribute_not_exists(userId)"
        )

        response_user = user_item.copy()
        response_user.pop("password")

        return {
            "statusCode": 201,
            "body": json.dumps({
                "message": "User registered successfully",
                "user": response_user
            })
        }

    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "DynamoDB error", "error": str(e)})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error", "error": str(e)})
        }