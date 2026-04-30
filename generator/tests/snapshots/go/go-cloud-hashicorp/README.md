# 🔐 my-cloud-hashicorp-go-client

Cloud/HashiCorp Vault Go demo client used in snapshot tests.

A generated CSFLE (Client-Side Field Level Encryption) demo client targeting **Confluent Cloud** with **HashiCorp Vault**.

## 📋 Prerequisites

* Go 1.22 or later
* A C toolchain (`confluent-kafka-go` wraps `librdkafka` via cgo)
  * macOS: install Xcode Command Line Tools (`xcode-select --install`)
  * Linux: install `gcc` and your distribution's `librdkafka-dev` package
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

### 1. Download Module Dependencies

```shell
go mod tidy
```

This downloads `confluent-kafka-go/v2` (Kafka client + Schema Registry + HashiCorp Vault encryption driver) and `godotenv`, and populates `go.sum`. The `// indirect` block in `go.mod` is also filled in based on the resolved transitive deps for your platform.

### 2. KMS Configuration

This client encrypts the `birthday` field using **HashiCorp Vault** (Transit secrets engine). You'll need:

* A **Vault server** reachable from this client (set `VAULT_ADDR`, e.g. `http://127.0.0.1:8200`).
* The **Transit secrets engine** enabled, with a key created at `transit/keys/<name>`. The KEK URL is then `<VAULT_ADDR>/transit/keys/<name>` — use this as `HCVAULT_KMS_KEY_ID`.
* A **Vault token** with `read` and `update` permissions on `transit/encrypt/<name>` and `transit/decrypt/<name>` (set `VAULT_TOKEN`).

> **Note:** the `kms.type` value is `hcvault` (no `-kms` suffix), unlike the other KMS providers.

### 3. Environment Variables

The generator wrote a `.env` file alongside `.env.example`. Open `.env` and replace any `<FILL_ME>` placeholders with real values.

> ⚠️ **Security:** Never commit the `.env` file — it contains sensitive credentials.
> 💡 **How it's loaded:** `internal/config/config.go` calls `godotenv.Load(...)` (non-clobbering), so variables already exported in your shell take precedence over `.env`. That's what makes the unauthorized-access trick below work.

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

1. Creates the Kafka topic `my-cloud-hashicorp-go-client-0040` (idempotent — safe to re-run).
2. Registers the schema for `my-cloud-hashicorp-go-client-0040-value` with the `birthday` field tagged as `PII`.
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
export VAULT_TOKEN="invalid"
export KAFKA_GROUP_ID="testing-invalid-key"

go run ./cmd/consumer
```

The `birthday` field will appear as ciphertext, demonstrating that consumers without KMS access cannot decrypt PII.

