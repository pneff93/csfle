# 🔐 my-cloud-hashicorp-client

Cloud/HashiCorp Vault demo client used in snapshot tests.

A generated CSFLE (Client-Side Field Level Encryption) demo client targeting **Confluent Cloud** with **HashiCorp Vault**.

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

This client encrypts the `birthday` field using **HashiCorp Vault** (Transit secrets engine). You'll need:

* A **Vault server** reachable from this client (set `VAULT_ADDR`, e.g. `http://127.0.0.1:8200`).
* The **Transit secrets engine** enabled, with a key created at `transit/keys/<name>`. The KEK URL is then `<VAULT_ADDR>/transit/keys/<name>` — use this as `HCVAULT_KMS_KEY_ID`.
* A **Vault token** with `read` and `update` permissions on `transit/encrypt/<name>` and `transit/decrypt/<name>` (set `VAULT_TOKEN`).

> **Note:** the `kms.type` value is `hcvault` (no `-kms` suffix), unlike the other KMS providers.

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

The script is identical across all generated client languages — topic creation runs in an inline Python heredoc (using `confluent-kafka` from the venv you set up above), schema and rule registration use plain `curl`. It:

1. Creates the Kafka topic `my-cloud-hashicorp-client-0008` (idempotent — safe to re-run).
2. Registers the schema for `my-cloud-hashicorp-client-0008-value` with the `birthday` field tagged as `PII`.
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
export VAULT_TOKEN="invalid"
export KAFKA_GROUP_ID="testing-invalid-key"

python avro_consumer.py
```

The `birthday` field will appear as ciphertext, demonstrating that consumers without KMS access cannot decrypt PII.

