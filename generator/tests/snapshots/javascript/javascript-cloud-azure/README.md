# 🔐 my-cloud-azure-js-client

Cloud/Azure JavaScript demo client used in snapshot tests.

A generated CSFLE (Client-Side Field Level Encryption) demo client targeting **Confluent Cloud** with **Azure Key Vault**.

## 📋 Prerequisites

* Node.js 18+ (LTS recommended) and npm
* `python` (3.8+) with `confluent-kafka` installed — used by `bootstrap.sh` for topic creation (`pip install confluent-kafka`)
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

### 1. Install npm Dependencies

```shell
npm install
```

This pulls in `@confluentinc/kafka-javascript` (which wraps `librdkafka` via native bindings), `@confluentinc/schemaregistry` (includes the Azure Key Vault encryption driver), and `dotenv`.

> 💡 **Note:** Pre-built `librdkafka` binaries are published for common platforms (macOS arm64/x64, Linux x64). If `npm install` falls back to building from source, you'll need a C++ toolchain (`xcode-select --install` on macOS, `build-essential` on Debian/Ubuntu).

### 2. KMS Configuration

This client encrypts the `birthday` field using **Azure Key Vault**. You'll need:

* An **Azure Key Vault** with an **RSA key** (the KEK). The key URL has the form `https://<vault-name>.vault.azure.net/keys/<key-name>/<version>`.
* An **App Registration** (service principal) with `Key Vault Crypto User` role on the vault.
* The service principal's **Tenant ID**, **Client ID**, and **Client Secret**.

The credentials are passed to `AvroSerializer` / `AvroDeserializer` via `ruleConfig` so the `AzureKmsDriver` constructs a `ClientSecretCredential` deterministically (rather than relying on Azure SDK defaults).

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
4. Define a tag named `PII` in the Schema Registry tag catalog before running `./bootstrap.sh`.

## 🏷️ Bootstrap

Create the Kafka topic, register the Avro schema, and register the field-encryption rule:

```shell
./bootstrap.sh
```

The script is identical across all generated client languages — topic creation runs in an inline Python heredoc (using `confluent-kafka`), schema and rule registration use plain `curl`. It:

1. Creates the Kafka topic `my-cloud-azure-js-client-0022` (idempotent — safe to re-run).
2. Registers the schema for `my-cloud-azure-js-client-0022-value` with the `birthday` field tagged as `PII`.
3. Registers an encryption rule that targets the `PII` tag, using your configured KEK.

## 🚀 Running the Demo

### Produce Encrypted Data

```shell
npm run produce
```

> 💡 **Or directly:** `node producer.js`

The `birthday` field is encrypted before the record is sent to Kafka. You can confirm by inspecting the message in Control Center / your Kafka UI — `birthday` will appear as base64 ciphertext.

### Consume with Valid Credentials

```shell
npm run consume
```

With valid KMS credentials in `.env`, the consumer decrypts `birthday` transparently.

### 🔒 Testing Unauthorized Access

Temporarily set invalid KMS credentials and a fresh consumer group:

```shell
export AZURE_CLIENT_SECRET="invalid"
export KAFKA_GROUP_ID="testing-invalid-key"

npm run consume
```

> 💡 **Why this works:** `dotenv` does not overwrite variables already set in the shell, so the `export`s above take precedence over the values in `.env`.

The `birthday` field will appear as ciphertext, demonstrating that consumers without KMS access cannot decrypt PII.

