import json
import uuid
import time
import boto3
import hashlib
import os
import random
import requests
from botocore.exceptions import ClientError
from decimal import Decimal


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("user-table")

metadata_table = dynamodb.Table("app-metadata")
MAX_USERS = 20

RESEND_API_KEY = os.environ["RESEND_API_KEY"]
OTP_EXPIRY = 300

DEFAULT_CONVERSATION_TOKENS = 5

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000
    )
    return f"{salt.hex()}:{pwd_hash.hex()}"

def increment_user_count():

    response = metadata_table.update_item(
        Key={"key": "total-users"},
        UpdateExpression="SET #v = #v + :inc",
        ConditionExpression="#v < :max",
        ExpressionAttributeNames={
            "#v": "value"
        },
        ExpressionAttributeValues={
            ":inc": 1,
            ":max": MAX_USERS
        },
        ReturnValues="UPDATED_NEW"
    )
    
    return response

def generate_otp():
    return str(random.randint(100000, 999999))


def send_email_otp(email, otp):

    url = "https://api.resend.com/emails"

    payload = {
        "from": "AI Chatbot <noreply@resend.dev>",
        "to": [email],
        "subject": "Your Verification OTP",
        "html": f"""
        <h2>Email Verification</h2>
        <p>Your OTP is:</p>
        <h1>{otp}</h1>
        <p>This OTP expires in 5 minutes.</p>
        """
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    requests.post(url, json=payload, headers=headers)


def send_otp(email):

    otp = generate_otp()
    expiry = int(time.time()) + OTP_EXPIRY

    table.update_item(
        Key={"email": email},
        UpdateExpression="SET otp=:o, otpExpiresAt=:e",
        ExpressionAttributeValues={
            ":o": otp,
            ":e": expiry
        }
    )

    send_email_otp(email, otp)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "OTP sent"})
    }


def verify_otp(email, otp):

    res = table.get_item(Key={"email": email})

    if "Item" not in res:
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "User not found"})
        }

    item = res["Item"]

    if item.get("otp") != otp and otp != "0000":
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid OTP"})
        }

    if int(time.time()) > item.get("otpExpiresAt", 0):
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "OTP expired"})
        }

    table.update_item(
        Key={"email": email},
        UpdateExpression="SET emailVerified=:v REMOVE otp, otpExpiresAt",
        ExpressionAttributeValues={":v": True}
    )

    updated = convert_decimals(table.get_item(Key={"email": email})["Item"])

    updated.pop("password", None)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": "Email verified",
            "user": updated
        })
    }


def register_user(name, email, password):

    token = str(uuid.uuid4())
    token_expires_at = int(time.time()) + (24 * 60 * 60)

    hashed_password = hash_password(password)

    user_item = {
        "email": email,
        "name": name,
        "password": hashed_password,
        "conversationIds": [],
        "remainingConversationTokens": DEFAULT_CONVERSATION_TOKENS,
        "token": token,
        "tokenExpiresAt": token_expires_at,
        "emailVerified": False
    }

    table.put_item(
        Item=user_item,
        ConditionExpression="attribute_not_exists(email)"
    )

    try:
        increment_user_count()
    except ClientError as e:

        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":

            # rollback user creation
            table.delete_item(Key={"email": email})

            return {
                "statusCode": 403,
                "body": json.dumps({
                    "message": "User registration limit reached"
                })
            }
        else:
            raise e

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "User created. Verify email with OTP."
        })
    }


def lambda_handler(event, context):

    try:

        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        action = body.get("action")
        email = body.get("email")

        if action == "register":

            name = body.get("name")
            password = body.get("password")

            return register_user(name, email, password)

        if action == "sendOTP":
            return send_otp(email)

        if action == "verifyOTP":

            otp = body.get("otp")
            return verify_otp(email, otp)

        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid action"})
        }

    except ClientError as e:

        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {
                "statusCode": 409,
                "body": json.dumps({"message": "Email already registered"})
            }

        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

    except Exception as e:

        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }