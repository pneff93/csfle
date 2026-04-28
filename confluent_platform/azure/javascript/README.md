# 🔐 Client-Side Field Level Encryption (CSFLE) with Confluent Platform and Azure Key Vault - JavaScript Client

This directory provides a Node.js (JavaScript) implementation of the Client-Side Field Level Encryption (CSFLE) demo
using Confluent Platform running locally with Docker Compose.

## 📋 Prerequisites

* Docker and Docker Compose
* Node.js 18 or later (LTS recommended) and npm
* Azure account with Key Vault access

## 🎯 Goal

We will produce personal data to a local Kafka topic in the following format:

```json
{
  "id": "1",
  "name": "Anna",
  "birthday": "2024-02-10",
  "timestamp": "2025-02-10T19:54:21.884Z"
}
```

The `birthday` field will be encrypted using CSFLE with Azure Key Vault. We'll then consume the data with proper
credentials to decrypt it, and simulate unauthorized access to demonstrate the security benefits.

## 🛠️ Setup

### 1. Install npm Dependencies

From the `javascript/` directory:

```shell
npm install
```

This pulls in `@confluentinc/kafka-javascript`, `@confluentinc/schemaregistry` (which includes the Azure Key Vault
encryption driver), and `dotenv`.

> 💡 **Note:** `@confluentinc/kafka-javascript` wraps `librdkafka` via native bindings. Pre-built binaries are published
> for common platforms. If `npm install` falls back to building from source, you'll need a C++ toolchain
> (`xcode-select --install` on macOS, `build-essential` on Debian/Ubuntu).

### 2. Azure Key Vault Configuration

For detailed instructions on creating an Azure App Registration, generating a Key Vault key, and assigning access
policies, please refer to the [Azure Key Vault Setup section](../python/README.md#2-azure-key-vault-configuration) in
the Python client's README — the steps are identical.

You'll need:

* Azure Key Vault Key Identifier (e.g., `https://my-vault.vault.azure.net/keys/my-key/abc123`)
* Azure Tenant ID
* Azure Client ID (the App Registration's application ID)
* Azure Client Secret (the secret value, not the secret ID)

### 3. Environment Variables

This client reads from the **same `.env` file** used by the Python client, located in the parent directory
(`confluent_platform/azure/.env`). If you haven't created it yet:

```shell
cd .. && cp .env.example .env && cd javascript
```

Edit `../.env` with your configuration values:

| Configuration                | Environment Variable      | Default/Example Value         |
|------------------------------|---------------------------|-------------------------------|
| **Kafka Topic**              | `KAFKA_TOPIC`             | `csfle-demo`                  |
| **Kafka Bootstrap Servers**  | `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9091`              |
| **Schema Registry URL**      | `SCHEMA_REGISTRY_URL`     | `http://localhost:8081`       |
| **Azure KMS Key Identifier** | `AZURE_KMS_KEY_ID`        | Your Key Vault Key ID         |
| **Azure KMS Key Name**       | `AZURE_KMS_KEY_NAME`      | `csfle-demo-kek`              |
| **Azure KMS Type**           | `AZURE_KMS_TYPE`          | `azure-kms`                   |
| **Azure Tenant ID**          | `AZURE_TENANT_ID`         | Your Azure Tenant ID          |
| **Azure Client ID**          | `AZURE_CLIENT_ID`         | Your Service Principal ID     |
| **Azure Client Secret**      | `AZURE_CLIENT_SECRET`     | Your Service Principal Secret |
| **Consumer Group ID**        | `KAFKA_GROUP_ID`          | `csfle-demo-consumer-group`   |
| **Auto Offset Reset**        | `KAFKA_AUTO_OFFSET_RESET` | `earliest`                    |

> ⚠️ **Security:** Never commit the `.env` file to version control as it contains sensitive credentials!
> 💡 **Note:** Confluent Platform runs locally using PLAINTEXT protocol (no SASL/SSL) for Kafka and no authentication for
> Schema Registry. However, Azure Key Vault is still used for field-level encryption.
> 💡 **How it's loaded:** `dotenv` reads `../.env` at startup. Variables already exported in your shell take precedence
> (default `dotenv` behavior — it does not overwrite existing env vars), which makes the unauthorized-access test below
> work.

### 4. Start Confluent Platform

```shell
cd ../..
docker compose up -d
```

Wait a few seconds for all services to start. You can also access [Control Center](http://localhost:9021/) to monitor
the cluster.

## 🏷️ Schema Configuration

### Load Environment Variables

```shell
cd azure/javascript
set -a
source ../.env
set +a
```

### Register the Schema

```shell
curl --location "$SCHEMA_REGISTRY_URL/subjects/$KAFKA_TOPIC-value/versions" \
--header 'Accept: application/vnd.schemaregistry.v1+json' \
--header 'Content-Type: application/json' \
--data '{
    "schemaType": "AVRO",
    "schema": "{  \"name\": \"PersonalData\", \"type\": \"record\", \"namespace\": \"com.csfleExample\", \"fields\": [{\"name\": \"id\", \"type\": \"string\"}, {\"name\": \"name\", \"type\": \"string\"},{\"name\": \"birthday\", \"type\": \"string\", \"confluent:tags\": [ \"PII\"]},{\"name\": \"timestamp\",\"type\": [\"string\", \"null\"]}]}"
}'
```

### Register the Encryption Rule

```shell
curl --location "$SCHEMA_REGISTRY_URL/subjects/$KAFKA_TOPIC-value/versions" \
--header 'Accept: application/vnd.schemaregistry.v1+json' \
--header 'Content-Type: application/json' \
--data '{
    "ruleSet": {
        "domainRules": [
            {
                "name": "encryptPII",
                "kind": "TRANSFORM",
                "type": "ENCRYPT",
                "mode": "WRITEREAD",
                "tags": [
                    "PII"
                ],
                "params": {
                    "encrypt.kek.name": "'"$AZURE_KMS_KEY_NAME"'",
                    "encrypt.kms.key.id": "'"$AZURE_KMS_KEY_ID"'",
                    "encrypt.kms.type": "'"$AZURE_KMS_TYPE"'"
                },
                "onFailure": "ERROR,NONE"
            }
        ]
    }
}'
```

### Verify Configuration

```shell
curl --request GET --url "$SCHEMA_REGISTRY_URL/subjects/$KAFKA_TOPIC-value/versions/latest" | jq
```

## 🚀 Running the Demo

### Produce Encrypted Data

```shell
set -a
source ../.env
set +a

npm run produce
```

> 💡 **Or directly:** `node producer.js`

✅ Expected output:

```log
Producing user records to topic csfle-demo. ^C to exit.
PersonalData record 1 successfully produced to csfle-demo [0] at offset 0
PersonalData record 2 successfully produced to csfle-demo [0] at offset 1
...
```

### Consume with Valid Credentials

```shell
npm run consume
```

✅ Expected output (decrypted birthday):

```log
--- Personal Data ---
  ID:        1
  Name:      Anna
  Birthday:  2025-02-10
  Timestamp: 2025-02-10T15:11:42.477Z
---------------------
...
```

Press `Ctrl+C` to stop the consumer.

### 🔒 Testing Unauthorized Access

```shell
export AZURE_CLIENT_SECRET="invalid_secret_key"
export KAFKA_GROUP_ID="testing-invalid-key"

npm run consume
```

🔴 Expected output (encrypted birthday remains encrypted):

```log
--- Personal Data ---
  ID:        1
  Name:      Anna
  Birthday:  yabvlkT//S+QDAXP7idIl3wU3pHR8/2oZZA8ORovepAun1eLORo=
  Timestamp: 2025-02-10T15:11:42.476Z
---------------------
```

✨ **This demonstrates that consumers without access to the KEK cannot decrypt fields protected by CSFLE**

### Restore Valid Credentials

```shell
unset AZURE_CLIENT_SECRET
unset KAFKA_GROUP_ID

set -a
source ../.env
set +a
```

## 🧹 Cleanup

```shell
cd ../..
docker compose down -v
```
