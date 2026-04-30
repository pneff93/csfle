# 🔐 my-platform-azure-client

Platform/Azure demo client used in snapshot tests.

A generated CSFLE (Client-Side Field Level Encryption) demo client targeting **Confluent Platform** with **Azure Key Vault**.

## 📋 Prerequisites

* Python 3.8+
* Docker and Docker Compose (for the local Confluent Platform stack)
* Access to your KMS provider with permission to use the configured KEK

## 🎯 Goal

Produce personal data records to a Kafka topic with the `birthday` field automatically encrypted via CSFLE:

```json
{
  "id": "1",
  "name": "Anna",
  "birthday": "2024-02-10",
  "timestamp": "2025-02-10T19:54:21.884Z"
}
```

Consumers with valid KMS credentials decrypt the field automatically; consumers without can only read the encrypted ciphertext.

## 🛠️ Setup

### 1. Python Environment

Create a virtual environment and install dependencies:

```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. KMS Configuration

This client encrypts the `birthday` field using **Azure Key Vault**. You'll need:

* An **Azure Key Vault** with an **RSA key** (the KEK). The key URL has the form `https://<vault-name>.vault.azure.net/keys/<key-name>/<version>`.
* An **App Registration** (service principal) with `Key Vault Crypto User` role on the vault.
* The service principal's **Tenant ID**, **Client ID**, and **Client Secret**.

The Azure KMS driver reads `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, and `AZURE_CLIENT_SECRET` from the process environment.

### 3. Environment Variables

Copy `.env.example` to `.env` (or edit the generated `.env` directly) and replace any `<FILL_ME>` placeholders:

```shell
cp .env.example .env
$EDITOR .env
```

> ⚠️ **Security:** Never commit the `.env` file — it contains sensitive credentials.

### 4. Start Confluent Platform

Start the local Confluent Platform stack (broker + Schema Registry + Control Center) using Docker Compose:

```shell
cd ../../confluent_platform
docker compose up -d
```

Wait a few seconds for all services to start. You can check the logs with `docker compose logs -f` or open [Control Center](http://localhost:9021/) in a browser.

## 🏷️ Bootstrap

Create the Kafka topic, register the Avro schema, and register the field-encryption rule:

```shell
./bootstrap.sh
```

The script sources `.env` and (with the venv active):

1. Creates the Kafka topic `my-platform-azure-client-0002` (idempotent — safe to re-run).
2. Registers the schema for `my-platform-azure-client-0002-value` with the `birthday` field tagged as `PII`.
3. Registers an encryption rule that targets the `PII` tag, using your configured KEK.

## 🚀 Running the Demo

### Produce Encrypted Data

```shell
python avro_producer.py
```

The `birthday` field is encrypted before the record is sent to Kafka. You can confirm by inspecting the message in Control Center / your Kafka UI — `birthday` will appear as base64 ciphertext.

### Consume with Valid Credentials

```shell
python avro_consumer.py
```

With valid KMS credentials in `.env`, the consumer decrypts `birthday` transparently.

### 🔒 Testing Unauthorized Access

Temporarily set invalid KMS credentials and a fresh consumer group:

```shell
export AZURE_CLIENT_SECRET="invalid"
export KAFKA_GROUP_ID="testing-invalid-key"

python avro_consumer.py
```

The `birthday` field will appear as ciphertext, demonstrating that consumers without KMS access cannot decrypt PII.

## 🧹 Cleanup

To stop and remove the Confluent Platform containers (and topic data):

```shell
cd ../../confluent_platform
docker compose down -v
```
