# 🔐 my-platform-aws-js-client

Platform/AWS JavaScript demo client used in snapshot tests.

A generated CSFLE (Client-Side Field Level Encryption) demo client targeting **Confluent Platform** with **AWS KMS**.

## 📋 Prerequisites

* Node.js 18+ (LTS recommended) and npm
* `python` (3.8+) with `confluent-kafka` installed — used by `bootstrap.sh` for topic creation (`pip install confluent-kafka`)
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

### 1. Install npm Dependencies

```shell
npm install
```

This pulls in `@confluentinc/kafka-javascript` (which wraps `librdkafka` via native bindings), `@confluentinc/schemaregistry` (includes the AWS KMS encryption driver), and `dotenv`.

> 💡 **Note:** Pre-built `librdkafka` binaries are published for common platforms (macOS arm64/x64, Linux x64). If `npm install` falls back to building from source, you'll need a C++ toolchain (`xcode-select --install` on macOS, `build-essential` on Debian/Ubuntu).

### 2. KMS Configuration

This client encrypts the `birthday` field using **AWS KMS**. You'll need:

* An **AWS KMS Key** (the KEK). Note the full ARN, e.g. `arn:aws:kms:eu-central-1:123456789:key/xxx-xxx-xxx`.
* An **IAM user or role** with `kms:Encrypt`, `kms:Decrypt`, and `kms:GenerateDataKey` permissions on that key.
* The IAM principal's **Access Key ID** and **Secret Access Key**.

The credentials are passed to `AvroSerializer` / `AvroDeserializer` via `ruleConfig` so the `AwsKmsDriver` reads them deterministically (rather than relying on the AWS SDK default credential chain).

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

The script is identical across all generated client languages — topic creation runs in an inline Python heredoc (using `confluent-kafka`), schema and rule registration use plain `curl`. It:

1. Creates the Kafka topic `my-platform-aws-js-client-0017` (idempotent — safe to re-run).
2. Registers the schema for `my-platform-aws-js-client-0017-value` with the `birthday` field tagged as `PII`.
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
export AWS_SECRET_ACCESS_KEY="invalid"
export KAFKA_GROUP_ID="testing-invalid-key"

npm run consume
```

> 💡 **Why this works:** `dotenv` does not overwrite variables already set in the shell, so the `export`s above take precedence over the values in `.env`.

The `birthday` field will appear as ciphertext, demonstrating that consumers without KMS access cannot decrypt PII.

## 🧹 Cleanup

To stop and remove the Confluent Platform containers (and topic data):

```shell
cd ../../confluent_platform
docker compose down -v
```
