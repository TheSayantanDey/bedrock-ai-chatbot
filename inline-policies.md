# 🔐 IAM Inline Policies – Least Privilege Design

This document defines the **least-privilege IAM inline policies** used for each AWS Lambda function in the AI-powered serverless chatbot architecture.

Each Lambda function is granted **only the minimum permissions required** to perform its task.

---

# 🧠 1️⃣ Model Invocation Lambda

**Purpose:**
Invokes Amazon Bedrock (Nova Micro) and updates conversation data in DynamoDB.

## Permissions Granted

* Invoke specific Bedrock foundation model
* Read & update conversation table
* Write logs to CloudWatch

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeModelAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:REGION::foundation-model/amazon.nova-micro-v1:0"
    },
    {
      "Sid": "DynamoDBConversationTableAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/conversation-table"
    },
    {
      "Sid": "CloudWatchLogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

> 🔎 Note: `logs:CreateLogGroup` can be removed if log groups are pre-created.

---

# 🆔 2️⃣ Generate Conversation ID Lambda

**Purpose:**
Creates a new conversation entry and updates user metadata.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "UserTableUpdateAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/user-table"
    },
    {
      "Sid": "ConversationTableWriteAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem"
      ],
      "Resource": "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/conversation-table"
    },
    {
      "Sid": "CloudWatchLogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

---

# 📜 3️⃣ Get Conversation History Lambda

**Purpose:**
Fetches conversation history for a user session.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "UserTableReadAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/user-table"
    },
    {
      "Sid": "ConversationTableReadAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:BatchGetItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/conversation-table",
        "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/conversation-table/index/*"
      ]
    },
    {
      "Sid": "CloudWatchLogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

---

# 🔑 4️⃣ Login Lambda

**Purpose:**
Validates user credentials and updates login metadata.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "UserTableReadAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/user-table"
    },
    {
      "Sid": "UserTableUpdateAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/user-table"
    },
    {
      "Sid": "CloudWatchLogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

---

# 📝 5️⃣ Register Lambda

**Purpose:**
Creates a new user in DynamoDB.
Keeps track of the total users
```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "UserTableAccess",
			"Effect": "Allow",
			"Action": [
				"dynamodb:PutItem",
				"dynamodb:UpdateItem",
				"dynamodb:GetItem",
				"dynamodb:DeleteItem"
			],
			"Resource": "arn:aws:dynamodb:us-east-1:771992991399:table/user-table"
		},
		{
			"Sid": "MetadataTableAccess",
			"Effect": "Allow",
			"Action": [
				"dynamodb:UpdateItem",
				"dynamodb:GetItem"
			],
			"Resource": "arn:aws:dynamodb:us-east-1:771992991399:table/app-metadata"
		},
		{
			"Sid": "CloudWatchLogsAccess",
			"Effect": "Allow",
			"Action": [
				"logs:CreateLogGroup",
				"logs:CreateLogStream",
				"logs:PutLogEvents"
			],
			"Resource": "*"
		}
	]
}
```

---

# 🛡 Security & Well-Architected Alignment

This IAM design follows:

* ✅ Principle of Least Privilege
* ✅ Resource-level restrictions
* ✅ Separation of concerns (per-function role design)
* ✅ No wildcard service permissions
* ✅ Scoped DynamoDB table access
* ✅ Specific Bedrock model ARN restriction

---