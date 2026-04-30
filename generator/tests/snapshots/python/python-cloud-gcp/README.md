# 🔐 my-cloud-gcp-client

Cloud/GCP demo client used in snapshot tests.

A generated CSFLE (Client-Side Field Level Encryption) demo client targeting **Confluent Cloud** with **Google Cloud KMS**.

## 📋 Prerequisites

* Python 3.8+
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

This client encrypts the `birthday` field using **Google Cloud KMS**. You'll need:

* A **Google Cloud KMS keyring + key** (the KEK). The resource ID has the form `projects/<project>/locations/<loc>/keyRings/<ring>/cryptoKeys/<key>`.
* A **service account** with `Cloud KMS CryptoKey Encrypter/Decrypter` role on that key.
* The service account's JSON key file. Open it and copy the four fields `client_id`, `client_email`, `private_key_id`, and `private_key` into your `.env`.

> ⚠️ **Do not append `/cryptoKeyVersions/N`** to `GCP_KMS_KEY_ID`. Version-scoped resources are encrypt-only and CSFLE will fail on the very first produce when it tries to decrypt the DEK. Use the `cryptoKey` itself.

> **Note on `GCP_PRIVATE_KEY`:** the value is a multi-line PEM string with literal `\n` escapes. Wrap it in double quotes in `.env` so `python-dotenv` preserves the newlines.

### 3. Environment Variables

Copy `.env.example` to `.env` (or edit the generated `.env` directly) and replace any `<FILL_ME>` placeholders:

```shell
cp .env.example .env
$EDITOR .env
```

> ⚠️ **Security:** Never commit the `.env` file — it contains sensitive credentials.

### 4. Confluent Cloud Setup

This client targets a **Confluent Cloud** cluster with **Advanced Stream Governance** enabled (required for CSFLE).

In the Confluent Cloud UI, you'll need to:

1. Create a Kafka cluster and an API key/secret pair (used as `KAFKA_SASL_USERNAME` / `KAFKA_SASL_PASSWORD`).
2. Note the bootstrap server URL (used as `KAFKA_BOOTSTRAP_SERVERS`).
3. Enable Schema Registry, then create a Schema Registry API key/secret. Concatenate them as `key:secret` for `SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO`.
4. Define a tag named `PII` in the Schema Registry tag catalog before running `register_schema.sh`.

## 🏷️ Bootstrap

Create the Kafka topic, register the Avro schema, and register the field-encryption rule:

```shell
./bootstrap.sh
```

The script sources `.env` and (with the venv active):

1. Creates the Kafka topic `my-cloud-gcp-client-0007` (idempotent — safe to re-run).
2. Registers the schema for `my-cloud-gcp-client-0007-value` with the `birthday` field tagged as `PII`.
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
export GCP_PRIVATE_KEY="invalid"
export KAFKA_GROUP_ID="testing-invalid-key"

python avro_consumer.py
```

The `birthday` field will appear as ciphertext, demonstrating that consumers without KMS access cannot decrypt PII.

