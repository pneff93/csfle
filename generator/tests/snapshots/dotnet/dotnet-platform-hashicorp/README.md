# 🔐 my-platform-hashicorp-dotnet-client

Platform/HashiCorp Vault .NET demo client used in snapshot tests.

A generated CSFLE (Client-Side Field Level Encryption) demo client targeting **Confluent Platform** with **HashiCorp Vault**.

## 📋 Prerequisites

* .NET SDK 8.0 or later
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

### 1. Build the projects

There's no top-level `.sln` in this generated project, so `dotnet build` needs an explicit project path. From the project root, build each runnable project (each transitively builds `Shared/` via its project reference):

```shell
dotnet build Producer
dotnet build Consumer
```

This restores all NuGet packages (including the `Confluent.SchemaRegistry.Encryption.*` driver) and compiles `Shared`, `Producer`, and `Consumer`.

> 💡 You can skip this step if you want — `dotnet run --project Producer` and `dotnet run --project Consumer` (used below) auto-restore and auto-build on first invocation. Building explicitly upfront just surfaces compile errors before you try to run.

### 2. KMS Configuration

This client encrypts the `birthday` field using **HashiCorp Vault** (Transit secrets engine). You'll need:

* A **Vault server** reachable from this client (set `VAULT_ADDR`, e.g. `http://127.0.0.1:8200`).
* The **Transit secrets engine** enabled, with a key created at `transit/keys/<name>`. The KEK URL is then `<VAULT_ADDR>/transit/keys/<name>` — use this as `HCVAULT_KMS_KEY_ID`.
* A **Vault token** with `read` and `update` permissions on `transit/encrypt/<name>` and `transit/decrypt/<name>` (set `VAULT_TOKEN`).

> **Note:** the `kms.type` value is `hcvault` (no `-kms` suffix), unlike the other KMS providers.

### 3. Environment Variables

The generator wrote a `.env` file alongside `.env.example`. Open `.env` and replace any `<FILL_ME>` placeholders with real values.

> ⚠️ **Security:** Never commit the `.env` file — it contains sensitive credentials.
> 💡 **How it's loaded:** `Shared/Config.cs` uses `DotNetEnv.Env.NoClobber().Load(...)`, so variables already exported in your shell take precedence over `.env`. That's what makes the unauthorized-access trick below work.

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

1. Creates the Kafka topic `my-platform-hashicorp-dotnet-client-0028` (idempotent — safe to re-run).
2. Registers the schema for `my-platform-hashicorp-dotnet-client-0028-value` with the `birthday` field tagged as `PII`.
3. Registers an encryption rule that targets the `PII` tag, using your configured KEK.

## 🚀 Running the Demo

### Produce Encrypted Data

```shell
dotnet run --project Producer
```

The `birthday` field is encrypted before the record is sent to Kafka. You can confirm by inspecting the message in Control Center / your Kafka UI — `birthday` will appear as base64 ciphertext.

### Consume with Valid Credentials

```shell
dotnet run --project Consumer
```

With valid KMS credentials in `.env`, the consumer decrypts `birthday` transparently.

### 🔒 Testing Unauthorized Access

Temporarily set invalid KMS credentials and a fresh consumer group:

```shell
export VAULT_TOKEN="invalid"
export KAFKA_GROUP_ID="testing-invalid-key"

dotnet run --project Consumer
```

The `birthday` field will appear as ciphertext, demonstrating that consumers without KMS access cannot decrypt PII.

## 🧹 Cleanup

To stop and remove the Confluent Platform containers (and topic data):

```shell
cd ../../confluent_platform
docker compose down -v
```
