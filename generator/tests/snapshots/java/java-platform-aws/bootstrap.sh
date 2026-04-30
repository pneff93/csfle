#!/usr/bin/env bash
#
# Bootstraps Kafka + Schema Registry for this CSFLE demo:
#   1. Creates the Kafka topic (idempotent, via BootstrapTopic.java)
#   2. Registers the Avro schema
#   3. Registers the field-encryption rule
#
# Run from the project directory:
#   ./bootstrap.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

set -a
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.env"
set +a

# ---------------------------------------------------------------------------
# 1. Create the Kafka topic (idempotent)
# ---------------------------------------------------------------------------
echo "Compiling project (so BootstrapTopic + Avro classes are built)..."
mvn -q compile

echo "Creating topic ${KAFKA_TOPIC}..."
mvn -q exec:java -Dexec.mainClass="com.example.app.BootstrapTopic"

# ---------------------------------------------------------------------------
# 2. Register the Avro schema
# ---------------------------------------------------------------------------
echo "Registering schema for ${KAFKA_TOPIC}-value..."
curl --fail --silent --show-error --location \
  "${SCHEMA_REGISTRY_URL}/subjects/${KAFKA_TOPIC}-value/versions" \
  --header 'Accept: application/vnd.schemaregistry.v1+json' \
  --header 'Content-Type: application/json' \
  --data '{
    "schemaType": "AVRO",
    "schema": "{ \"name\": \"PersonalData\", \"type\": \"record\", \"namespace\": \"com.csfleExample\", \"fields\": [{\"name\": \"id\", \"type\": \"string\"}, {\"name\": \"name\", \"type\": \"string\"}, {\"name\": \"birthday\", \"type\": \"string\", \"confluent:tags\": [\"PII\"]}, {\"name\": \"timestamp\", \"type\": [\"string\", \"null\"]}]}"
  }'
echo

# ---------------------------------------------------------------------------
# 3. Register the field-encryption rule
# ---------------------------------------------------------------------------
echo "Registering encryption rule..."
curl --fail --silent --show-error --location \
  "${SCHEMA_REGISTRY_URL}/subjects/${KAFKA_TOPIC}-value/versions" \
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
          "tags": ["PII"],
          "params": {
            "encrypt.kek.name": "'"${AWS_KMS_KEY_NAME}"'",
            "encrypt.kms.key.id": "'"${AWS_KMS_KEY_ID}"'",
            "encrypt.kms.type": "'"${AWS_KMS_TYPE}"'"
          },
          "onFailure": "ERROR,NONE"
        }
      ]
    }
  }'
echo

echo "Done."
