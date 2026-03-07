# 🚀 Project Setup Guide

This document explains how to set up the required AWS resources for the project.

---

# 1️⃣ DynamoDB Setup

Create the required DynamoDB tables:

### 📌 Create `conversation-table`

1. Go to **AWS Console → DynamoDB → Tables**
2. Click **Create table**
3. Configure:

   * **Table name:** `conversation-table`
   * **Partition key:** `conversationId`
4. Click **Create**

---
### 📌 Create `user-table`

1. Go to **AWS Console → DynamoDB → Tables**
2. Click **Create table**
3. Configure:

   * **Table name:** `user-table`
   * **Partition key:** `email`
4. Click **Create**

---
### 📌 Create `app-metadata`

1. Go to **AWS Console → DynamoDB → Tables**
2. Click **Create table**
3. Configure:

   * **Table name:** `app-metadata`
   * **Partition key:** `key`
4. Click **Create**
5. Add an entry → `key`: total-users & `value`: 0


---

# 2️⃣ Lambda Setup

Create the following Lambda functions.

> ✅ Runtime for all functions: **Python 3.14**

For each function:

* Go to **AWS Console → Lambda → Create Function**
* Choose **Author from scratch**
* Set function name
* Select **Python 3.14**
* Click **Create Function**
* Paste the respective code file
* Click **Deploy**
* Go to **Configuration → Permissions**
* Add **least-privilege inline policy** (Refer to `inline-policies.md`)

---

### 🔹 1. ModelInvocation

* Code file: `modelInvocation.py`

### 🔹 2. generate-conversation-id

* Code file: `generateConvId.py`

### 🔹 3. get-conversation-history

* Code file: `getHistory.py`

### 🔹 4. login

* Code file: `login.py`

### 🔹 5. register

* Code file: `register.py`
- For register only, create an empty folder locally, run the command `pip install requests -t .` 
- Create a file `lambda_function.py` and put the code there. 
- Compress the file into a `.zip` and then upload the compressed file in code section. 
---

# 3️⃣ API Gateway Setup

You need to create **two REST APIs**:

* Conversation API
* Auth API

---

# 🔷 A. Create Conversation API

### Step 1: Create API

1. Go to **AWS Console → API Gateway**
2. Click **Create API**
3. Select **REST API**
4. Configure:

   * **API Name:** `Conversation`
   * **Description:** Conversation-related APIs
   * **Security Policy:** `SecurityPolicy_TLS13_1_2_2021_06`
5. Click **Create API**
6. Enable **CORS**

---

## Create Resources & Methods

### 🔹 1. `modelinvoke`

* Create Resource:

  * Resource name: `modelinvoke`
  * Enable CORS
* Create Method:

  * Method: `POST`
  * Integration type: `Lambda Function`
  * Select `ModelInvocation`

---

### 🔹 2. `generateconvoid`

* Create Resource:

  * Resource name: `generateconvoid`
  * Enable CORS
* Create Method:

  * Method: `POST`
  * Integration type: `Lambda Function`
  * Select `generate-conversation-id`

---

### 🔹 3. `gethistory`

* Create Resource:

  * Resource name: `gethistory`
  * Enable CORS
* Create Method:

  * Method: `POST`
  * Integration type: `Lambda Function`
  * Select `get-conversation-history`

---

## Deploy Conversation API

1. Select `/` and all created resources
2. Enable **CORS** (Allow all checkboxes)
3. Click **Deploy API**
4. Note the **Invoke URL**

---

# 🔷 B. Create Auth API

### Step 1: Create API

1. Go to **AWS Console → API Gateway**
2. Click **Create API**
3. Select **REST API**
4. Configure:

   * **API Name:** `Auth`
   * **Description:** Authentication-related APIs
   * **Security Policy:** `SecurityPolicy_TLS13_1_2_2021_06`
5. Click **Create**
6. Enable **CORS**

---

## Create Resources & Methods

### 🔹 1. `login`

* Create Resource:

  * Resource name: `login`
  * Enable CORS
* Create Method:

  * Method: `POST`
  * Integration type: `Lambda Function`
  * Select `login`

---

### 🔹 2. `register`

* Create Resource:

  * Resource name: `register`
  * Enable CORS
* Create Method:

  * Method: `POST`
  * Integration type: `Lambda Function`
  * Select `register`

---

## Deploy Auth API

1. Select `/` and all created resources
2. Enable **CORS** (Allow all checkboxes)
3. Click **Deploy API**
4. Note the **Invoke URL**

---

# 4️⃣ Environment Setup

1. Copy all **Invoke URLs** from deployed APIs.
2. Add them to your `.env` file with the correct paths.
3. Verify endpoints are correctly mapped.

✅ Your APIs are now ready to use!