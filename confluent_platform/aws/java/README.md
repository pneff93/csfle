# 🔐 Client-Side Field Level Encryption (CSFLE) with Confluent Platform and AWS KMS - Java Client

This directory provides a Java implementation of the Client-Side Field Level Encryption (CSFLE) demo using Confluent
Platform running locally with Docker Compose.

## 📋 Prerequisites

* Docker and Docker Compose
* Java 17 or later
* Maven 3.6 or later
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

### 1. Java and Maven

Ensure you have Java 17 and Maven installed:

```shell
java -version
mvn -version
```

### 2. AWS KMS Configuration

For detailed instructions on setting up AWS KMS, creating an IAM user, and obtaining credentials, please refer to
the [AWS KMS Setup section](../README.md#aws-kms-setup) in the parent README.

You'll need:

* AWS KMS Key ARN (e.g., `arn:aws:kms:eu-central-1:123456789:key/xxx-xxx-xxx`)
* AWS Access Key ID
* AWS Secret Access Key

### 3. Environment Variables

Copy the example environment file from the parent directory (shared with the Python client) and configure it with your
credentials:

```shell
cd .. && cp .env.example .env && cd java
```

Edit `../.env` with your configuration values:

| Configuration               | Environment Variable      | Example Value               |
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

### 4. Start Confluent Platform

From the parent directory, start Confluent Platform using Docker Compose:

```shell
cd ../..
docker compose up -d
```

Wait a few seconds for all services to start. You can check the logs:

```shell
docker compose logs -f
```

You can also access [Control Center](http://localhost:9021/) to monitor the cluster.

### 5. Build the Project

Compile the Java project and generate Avro classes:

```shell
mvn clean compile
```

## 🏷️ Schema Configuration

### Load Environment Variables

Before running the schema registration commands, load your configuration:

```shell
# Make sure you're in the java directory
cd java

# Load environment variables from parent directory's .env file
set -a
source ../.env
set +a
```

> 💡 **Tip:** The `set -a` and `set +a` commands enable/disable automatic export of variables. You only need to source
> the environment once per shell session. **Note:** Exported variables only affect the current terminal session and
> don't
> persist across different terminals.

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

### Register KEK and DEK (Optional)

You can have control of the KEK and DEK registration and rotation, but their registration will also be triggered by the
client if needed.

```shell
register-deks $SCHEMA_REGISTRY_URL $KAFKA_TOPIC-value
```

## 🚀 Running the Demo

### Produce Encrypted Data

Ensure your environment variables are loaded (if you haven't already):

```shell
set -a
source ../.env
set +a
```

Run the producer to send data with encrypted fields:

```shell
mvn exec:java -Dexec.mainClass="com.example.app.BasicProducer"
```

✅ Expected output:

```log
13:32:58.020 [kafka-producer-network-thread | MY_CLIENT] INFO  com.example.app.BasicProducer - Topic: csfle-demo - Partition {"id": "0", "name": "Anna", "birthday": "mZ+0MSFBYa7tYbS5+17QpnFIIRCcibFE9JW54dOK/Oxh9d0c2ls=", "timestamp": "2026-02-10"}
13:33:00.012 [kafka-producer-network-thread | MY_CLIENT] INFO  com.example.app.BasicProducer - Topic: csfle-demo - Partition {"id": "1", "name": "Anna", "birthday": "2JOHJtmnKeciS1PwPB/itrSkUcMS3wSX8YIKb/zOqR0NIEue7mg=", "timestamp": "2026-02-10"}...
```

> 💡 **Note:** The `birthday` field is encrypted before being sent to Kafka. The log output above shows the plaintext
> values before encryption.

You can view the encrypted messages in [Control Center](http://localhost:9021/) - the `birthday` field should appear
encrypted.

### Consume with Valid Credentials

Run the consumer with valid AWS credentials to see decrypted data:

```shell
mvn exec:java -Dexec.mainClass="com.example.app.BasicConsumer"
```

✅ Expected output (decrypted birthday):

```log
13:34:04.688 [com.example.app.BasicConsumer.main()] INFO  com.example.app.BasicConsumer - Consumed message: key=1, value={"id": "1", "name": "Anna", "birthday": "2025-02-10", "timestamp": "2026-02-10"}, partition=0, offset=33
13:34:04.688 [com.example.app.BasicConsumer.main()] INFO  com.example.app.BasicConsumer - Consumed message: key=2, value={"id": "2", "name": "Anna", "birthday": "2024-02-10", "timestamp": "2026-02-10"}, partition=0, offset=34
13:34:04.688 [com.example.app.BasicConsumer.main()] INFO  com.example.app.BasicConsumer - Consumed message: key=3, value={"id": "3", "name": "Anna", "birthday": "2023-02-10", "timestamp": "2026-02-10"}, partition=0, offset=35
...
Bye
```

### 🔒 Testing Unauthorized Access

Simulate a scenario where a client **without access to the KEK** tries to consume the encrypted data by temporarily
setting invalid AWS credentials:

```shell
# Temporarily override AWS credentials with invalid values
export AWS_SECRET_ACCESS_KEY="invalid_secret_key"
# Change the consumer group ID to re-consume all messages from the topic
export KAFKA_GROUP_ID="testing-invalid-key"

# Run the consumer - it will fail to decrypt the encrypted fields
mvn exec:java -Dexec.mainClass="com.example.app.BasicConsumer"
```

🔴 Expected output (encrypted birthday remains encrypted):

```log
13:34:04.688 [com.example.app.BasicConsumer.main()] INFO  com.example.app.BasicConsumer - Consumed message: key=3, value={"id": "3", "name": "Anna", "birthday": "4PstrAU4dwSFCsxzvfHdepZDaRtcoQ5wfCLt75WUMpT6kHpGZ3w=", "timestamp": "2026-02-10"}, partition=0, offset=35
...
```

✨ **This demonstrates that consumers without access to the KEK cannot decrypt fields protected by CSFLE**

### Restore Valid Credentials

To restore your correct AWS credentials for subsequent operations:

```shell
# Re-load environment variables from parent .env to restore correct credentials
set -a
source ../.env
set +a
```

> 💡 **Remember:** Exported variables only affect the current terminal session. If you open a new terminal, you'll need
> to source `../.env` again.

## 🧹 Cleanup

To stop and remove all Confluent Platform containers:

```shell
cd ../..
docker compose down -v
```

The `-v` flag removes volumes, which will delete all topic data and Schema Registry data.
