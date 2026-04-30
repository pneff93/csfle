# 🔐 my-platform-gcp-go-client

Platform/GCP Go demo client used in snapshot tests.

A generated CSFLE (Client-Side Field Level Encryption) demo client targeting **Confluent Platform** with **Google Cloud KMS**.

## 📋 Prerequisites

* Go 1.22 or later
* A C toolchain (`confluent-kafka-go` wraps `librdkafka` via cgo)
  * macOS: install Xcode Command Line Tools (`xcode-select --install`)
  * Linux: install `gcc` and your distribution's `librdkafka-dev` package
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

### 1. Download Module Dependencies

```shell
go mod tidy
```

This downloads `confluent-kafka-go/v2` (Kafka client + Schema Registry + Google Cloud KMS encryption driver) and `godotenv`, and populates `go.sum`. The `// indirect` block in `go.mod` is also filled in based on the resolved transitive deps for your platform.

### 2. KMS Configuration

This client encrypts the `birthday` field using **Google Cloud KMS**. You'll need:

* A **Google Cloud KMS keyring + key** (the KEK). The resource ID has the form `projects/<project>/locations/<loc>/keyRings/<ring>/cryptoKeys/<key>`.
* A **service account** with `Cloud KMS CryptoKey Encrypter/Decrypter` role on that key.
* The service account's JSON key file. Open it and copy the four fields `client_id`, `client_email`, `private_key_id`, and `private_key` into your `.env`.

> ⚠️ **Do not append `/cryptoKeyVersions/N`** to `GCP_KMS_KEY_ID`. Version-scoped resources are encrypt-only and CSFLE will fail on the very first produce when it tries to decrypt the DEK. Use the `cryptoKey` itself.

> **Note on `GCP_PRIVATE_KEY`:** the value is a multi-line PEM string with literal `\n` escapes. Wrap it in double quotes in `.env` so `godotenv` preserves it as a single string; `GetGcpRuleConfig` then converts the `\n` escapes into real newlines before handing the key to the driver.

### 3. Environment Variables

The generator wrote a `.env` file alongside `.env.example`. Open `.env` and replace any `<FILL_ME>` placeholders with real values.

> ⚠️ **Security:** Never commit the `.env` file — it contains sensitive credentials.
> 💡 **How it's loaded:** `internal/config/config.go` calls `godotenv.Load(...)` (non-clobbering), so variables already exported in your shell take precedence over `.env`. That's what makes the unauthorized-access trick below work.

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

1. Creates the Kafka topic `my-platform-gcp-go-client-0035` (idempotent — safe to re-run).
2. Registers the schema for `my-platform-gcp-go-client-0035-value` with the `birthday` field tagged as `PII`.
3. Registers an encryption rule that targets the `PII` tag, using your configured KEK.

## 🚀 Running the Demo

### Produce Encrypted Data

```shell
go run ./cmd/producer
```

> 💡 **Build a binary instead:** `go build -o bin/producer ./cmd/producer && ./bin/producer`

The `birthday` field is encrypted before the record is sent to Kafka. You can confirm by inspecting the message in Control Center / your Kafka UI — `birthday` will appear as base64 ciphertext.

### Consume with Valid Credentials

```shell
go run ./cmd/consumer
```

With valid KMS credentials in `.env`, the consumer decrypts `birthday` transparently.

### 🔒 Testing Unauthorized Access

Temporarily set invalid KMS credentials and a fresh consumer group:

```shell
export GCP_PRIVATE_KEY="invalid"
export KAFKA_GROUP_ID="testing-invalid-key"

go run ./cmd/consumer
```

The `birthday` field will appear as ciphertext, demonstrating that consumers without KMS access cannot decrypt PII.

## 🧹 Cleanup

To stop and remove the Confluent Platform containers (and topic data):

```shell
cd ../../confluent_platform
docker compose down -v
```
