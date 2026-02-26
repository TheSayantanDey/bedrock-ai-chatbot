import json
import uuid
import time
import boto3
import hashlib
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("user-table")


def verify_password(stored_password: str, provided_password: str) -> bool:
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

        # ✅ Get user by email (NO SCAN)
        response = table.get_item(
            Key={"email": email}
        )

        user = response.get("Item")

        if not user:
            return {
                "statusCode": 401,
                "body": json.dumps({
                    "message": "Invalid email or password"
                })
            }

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

        # 📝 Update token
        table.update_item(
            Key={"email": email},
            UpdateExpression="SET #t = :t, tokenExpiresAt = :e",
            ExpressionAttributeNames={
                "#t": "token"
            },
            ExpressionAttributeValues={
                ":t": new_token,
                ":e": new_expiry
            }
        )

        # Remove password before response
        user.pop("password", None)
        user["token"] = new_token
        user["tokenExpiresAt"] = new_expiry

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Login successful",
                "user": user
            }, default=str)
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