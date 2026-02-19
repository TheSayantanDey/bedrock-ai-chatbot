import json
import uuid
import time
import boto3
import hashlib
import os
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("user-table")

SECRET_KEY = "sayantan-1q2w3e4r"


def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    stored_password format: salt:hash
    """
    salt_hex, hash_hex = stored_password.split(":")
    salt = bytes.fromhex(salt_hex)

    new_hash = hashlib.pbkdf2_hmac(
        "sha256",
        provided_password.encode("utf-8"),
        salt,
        100_000
    )

    return new_hash.hex() == hash_hex


def lambda_handler(event, context):
    try:
        # Handle API Gateway & Lambda test events
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        email = body.get("email")
        password = body.get("password")

        if not email or not password:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "email and password are required"
                })
            }

        # 🔍 Find user by email (SCAN)
        response = table.scan(
            FilterExpression=Attr("email").eq(email)
        )

        if not response["Items"]:
            return {
                "statusCode": 401,
                "body": json.dumps({
                    "message": "Invalid email or password"
                })
            }

        user = response["Items"][0]

        # 🔐 Verify password
        if not verify_password(user["password"], password):
            return {
                "statusCode": 401,
                "body": json.dumps({
                    "message": "Invalid email or password"
                })
            }

        # 🔑 Generate new token
        new_token = str(uuid.uuid4())
        new_expiry = int(time.time()) + (24 * 60 * 60)

        # 📝 Update token in DynamoDB
        table.update_item(
            Key={"userId": user["userId"]},
            UpdateExpression="SET #t = :t, tokenExpiresAt = :e",
            ExpressionAttributeNames={
                "#t": "token"
            },
            ExpressionAttributeValues={
                ":t": new_token,
                ":e": new_expiry
            }
        )

        # Prepare response (remove password)
        user_response = user.copy()
        user_response.pop("password")
        user_response["token"] = new_token
        user_response["tokenExpiresAt"] = new_expiry

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Login successful",
                "user": user_response
            })
        }

    except ClientError as e:
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