# 🔐 Client-Side Field Level Encryption (CSFLE) with Confluent Platform and AWS KMS - .NET Client

This directory provides a .NET (C#) implementation of the Client-Side Field Level Encryption (CSFLE) demo using
Confluent Platform running locally with Docker Compose.

## 📋 Prerequisites

* Docker and Docker Compose
* [.NET SDK 8.0](https://dotnet.microsoft.com/download) or later
* AWS account with KMS access

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

The `birthday` field will be encrypted using CSFLE with AWS KMS. We'll then consume the data with proper credentials to
decrypt it, and simulate unauthorized access to demonstrate the security benefits.

## 🛠️ Setup

### 1. Restore NuGet Packages

From the `dotnet/` directory, restore dependencies for both projects:

```shell
dotnet restore Producer/Producer.csproj
dotnet restore Consumer/Consumer.csproj
```

This pulls in `Confluent.Kafka`, `Confluent.SchemaRegistry.Serdes.Avro`, `Confluent.SchemaRegistry.Encryption.Aws`, and
`DotNetEnv`.

> 💡 **Tip:** `dotnet build Producer/Producer.csproj` will also restore packages as part of compiling.

### 2. AWS KMS Configuration

For detailed instructions on setting up AWS KMS, creating an IAM user, and obtaining credentials, please refer to
the [AWS KMS Setup section](../README.md#aws-kms-setup) in the parent README.

You'll need:

* AWS KMS Key ARN (e.g., `arn:aws:kms:eu-central-1:123456789:key/xxx-xxx-xxx`)
* AWS Access Key ID
* AWS Secret Access Key

### 3. Environment Variables

This client reads from the **same `.env` file** used by the Python, Java, and Go clients, located in the parent
directory (`confluent_platform/aws/.env`). If you haven't created it yet:

```shell
cd .. && cp .env.example .env && cd dotnet
```

Edit `../.env` with your configuration values:

| Configuration               | Environment Variable      | Default/Example Value       |
|-----------------------------|---------------------------|-----------------------------|
| **Kafka Topic**             | `KAFKA_TOPIC`             | `csfle-demo`                |
| **Kafka Bootstrap Servers** | `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9091`            |
| **Schema Registry URL**     | `SCHEMA_REGISTRY_URL`     | `http://localhost:8081`     |
| **AWS KMS Key ARN**         | `AWS_KMS_KEY_ID`          | Your KMS Key ARN            |
| **AWS KMS Key Name**        | `AWS_KMS_KEY_NAME`        | `csfle-demo-kek`            |
| **AWS KMS Type**            | `AWS_KMS_TYPE`            | `aws-kms`                   |
| **AWS Access Key ID**       | `AWS_ACCESS_KEY_ID`       | Your AWS Access Key         |
| **AWS Secret Access Key**   | `AWS_SECRET_ACCESS_KEY`   | Your AWS Secret Key         |
| **Consumer Group ID**       | `KAFKA_GROUP_ID`          | `csfle-demo-consumer-group` |
| **Auto Offset Reset**       | `KAFKA_AUTO_OFFSET_RESET` | `earliest`                  |

> ⚠️ **Security:** Never commit the `.env` file to version control as it contains sensitive credentials!
> 💡 **Note:** Confluent Platform runs locally using PLAINTEXT protocol (no SASL/SSL) for Kafka and no authentication for
> Schema Registry. However, AWS KMS is still used for field-level encryption.
> 💡 **How it's loaded:** The .NET program uses `DotNetEnv` to read `../.env` at startup. Variables already exported in
> your shell take precedence (the loader is configured with `clobberExistingVars: false`) — useful for the
> unauthorized-access test below.

### 4. Start Confluent Platform

From the parent directory, start Confluent Platform using Docker Compose:

```shell
cd ..
docker compose up -d
```

Wait a few seconds for all services to start. You can check the logs:

```shell
docker compose logs -f
```

You can also access [Control Center](http://localhost:9021/) to monitor the cluster.

## 🏷️ Schema Configuration

### Load Environment Variables

Before running the schema registration commands, load your configuration:

```shell
# Make sure you're in the dotnet directory
cd dotnet

# Load environment variables from parent directory's .env file
set -a
source ../.env
set +a
```

> 💡 **Tip:** The `set -a` and `set +a` commands enable/disable automatic export of variables. You only need to source
> the environment once per shell session. **Note:** Exported variables only affect the current terminal session and
> don't persist across different terminals.

### Register the Schema

Register the Avro schema with the `PII` tag applied to the `birthday` field:

```shell
curl --location "$SCHEMA_REGISTRY_URL/subjects/$KAFKA_TOPIC-value/versions" \
--header 'Accept: application/vnd.schemaregistry.v1+json' \
--header 'Content-Type: application/json' \
--data '{
    "schemaType": "AVRO",
    "schema": "{  \"name\": \"PersonalData\", \"type\": \"record\", \"namespace\": \"com.csfleExample\", \"fields\": [{\"name\": \"id\", \"type\": \"string\"}, {\"name\": \"name\", \"type\": \"string\"},{\"name\": \"birthday\", \"type\": \"string\", \"confluent:tags\": [ \"PII\"]},{\"name\": \"timestamp\",\"type\": [\"string\", \"null\"]}]}"
}'
```

> 💡 **Note:** Unlike Confluent Cloud, there's no need to create a PII tag in Schema Registry first. The local Schema
> Registry accepts tags directly in the schema.

### Register the Encryption Rule

Define the encryption rule for all fields tagged with `PII`:

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
                    "encrypt.kek.name": "'"$AWS_KMS_KEY_NAME"'",
                    "encrypt.kms.key.id": "'"$AWS_KMS_KEY_ID"'",
                    "encrypt.kms.type": "'"$AWS_KMS_TYPE"'"
                },
                "onFailure": "ERROR,NONE"
            }
        ]
    }
}'
```

> 💡 **Tip:** The pattern `"'"$VARIABLE"'"` is necessary to interpolate shell variables inside JSON strings. It works by
> ending the single-quoted JSON string, adding a double-quoted variable, then starting the single-quoted string again.

### Verify Configuration

Check that everything is registered correctly:

```shell
curl --request GET \
  --url "$SCHEMA_REGISTRY_URL/subjects/$KAFKA_TOPIC-value/versions/latest" | jq
```

You can also verify in [Control Center](http://localhost:9021/) by navigating to Topics → Your Topic → Schema.

## 🚀 Running the Demo

### Produce Encrypted Data

Ensure your environment variables are loaded (if you haven't already):

```shell
set -a
source ../.env
set +a
```

Run the producer to send data with the encrypted `birthday` field:

```shell
dotnet run --project Producer
```

✅ Expected output:

```log
Producing user records to topic csfle-demo. ^C to exit.
PersonalData record 1 successfully produced to csfle-demo [0] at offset 0
PersonalData record 2 successfully produced to csfle-demo [0] at offset 1
PersonalData record 3 successfully produced to csfle-demo [0] at offset 2
...
```

You can view the encrypted messages in [Control Center](http://localhost:9021/) - the `birthday` field should appear
encrypted.

### Consume with Valid Credentials

Run the consumer with valid AWS credentials to see decrypted data:

```shell
dotnet run --project Consumer
```

✅ Expected output (decrypted birthday):

```log
--- Personal Data ---
  ID:        1
  Name:      Anna
  Birthday:  2025-02-10
  Timestamp: 2025-02-10T15:11:42.477591Z
---------------------
--- Personal Data ---
  ID:        2
  Name:      Anna
  Birthday:  2024-02-10
  Timestamp: 2025-02-10T15:11:42.478123Z
---------------------
...
```

Press `Ctrl+C` to stop the consumer.

### 🔒 Testing Unauthorized Access

Simulate a scenario where a client **without access to the KEK** tries to consume the encrypted data by temporarily
setting invalid AWS credentials:

```shell
# Temporarily override AWS credentials with invalid values
export AWS_SECRET_ACCESS_KEY="invalid_secret_key"
# Change the consumer group ID to re-consume all the messages from the topic
export KAFKA_GROUP_ID="testing-invalid-key"

# Run the consumer - it will fail to decrypt the birthday field
dotnet run --project Consumer
```

> 💡 **Why this works:** `DotNetEnv` is loaded with `.NoClobber()`, so the `export`s above take precedence over the
> values in `../.env`.

🔴 Expected output (encrypted birthday remains encrypted):

```log
--- Personal Data ---
  ID:        1
  Name:      Anna
  Birthday:  yabvlkT//S+QDAXP7idIl3wU3pHR8/2oZZA8ORovepAun1eLORo=
  Timestamp: 2025-02-10T15:11:42.476313Z
---------------------
```

✨ **This demonstrates that consumers without access to the KEK cannot decrypt fields protected by CSFLE**

### Restore Valid Credentials

To restore your correct AWS credentials for subsequent operations:

```shell
# Unset the overrides so the values from ../.env take effect again
unset AWS_SECRET_ACCESS_KEY
unset KAFKA_GROUP_ID

# Or re-load environment variables from parent .env
set -a
source ../.env
set +a
```

> 💡 **Remember:** Exported variables only affect the current terminal session. If you open a new terminal, you'll need
> to source `.env` again.

## 🗂️ Project Layout

```
dotnet/
├── avro/
│   └── personal_data.avsc          # Avro schema (registered via curl, also loaded by the producer
│                                   # to construct GenericRecord values)
├── Shared/
│   ├── Shared.csproj               # Shared library
│   └── Config.cs                   # Reads ../.env via DotNetEnv, validates required vars
├── Producer/
│   ├── Producer.csproj
│   └── Program.cs                  # Produces 20 encrypted records as Avro GenericRecords
└── Consumer/
    ├── Consumer.csproj
    └── Program.cs                  # Decrypts and prints records
```

This example uses the **Avro Generic** approach (`Avro.Generic.GenericRecord`) so no Avro code generation step is
required — the schema is loaded from `personal_data.avsc` at runtime, and fields are accessed by name. The wire-format
schema and the encryption rule are fetched from Schema Registry (because we set `AutoRegisterSchemas = false` and
`UseLatestVersion = true` on the serializer).

## 🧹 Cleanup

To stop and remove all Confluent Platform containers:

```shell
cd ..
docker compose down -v
```

The `-v` flag removes volumes, which will delete all topic data and Schema Registry data.
