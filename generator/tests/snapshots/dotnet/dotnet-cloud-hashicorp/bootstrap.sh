#!/usr/bin/env bash
#
# Bootstraps Kafka + Schema Registry for this CSFLE demo:
#   1. Creates the Kafka topic (idempotent)
#   2. Registers the Avro schema
#   3. Registers the field-encryption rule
#
# This script is intentionally identical across all generated client
# languages — topic creation runs in an inline Python heredoc so we don't
# need a per-language admin client. Schema + rule registration are pure curl.
#
# Prerequisites:
#   • bash, curl
#   • python (3.8+) with `confluent-kafka` installed
#       pip install confluent-kafka         # or use a venv if you prefer
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
echo "Creating topic ${KAFKA_TOPIC}..."
python - <<'PYEOF'
import os
import sys

from confluent_kafka.admin import AdminClient, NewTopic

admin_conf = {"bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"]}
admin_conf.update({
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
    "sasl.username": os.environ["KAFKA_SASL_USERNAME"],
    "sasl.password": os.environ["KAFKA_SASL_PASSWORD"],
})

admin = AdminClient(admin_conf)
topic = NewTopic(
    os.environ["KAFKA_TOPIC"],
    num_partitions=1,
    replication_factor=3,
)

for name, future in admin.create_topics([topic]).items():
    try:
        future.result()
        print(f"  created {name}")
    except Exception as exc:
        if "already exists" in str(exc).lower():
            print(f"  {name} already exists")
        else:
            print(f"  failed to create {name}: {exc}", file=sys.stderr)
            sys.exit(1)
PYEOF

# ---------------------------------------------------------------------------
# 2. Register the Avro schema
# ---------------------------------------------------------------------------
echo "Registering schema for ${KAFKA_TOPIC}-value..."
curl --fail --silent --show-error --location \
  "${SCHEMA_REGISTRY_URL}/subjects/${KAFKA_TOPIC}-value/versions" \
  --header "Authorization: Basic $(printf '%s' "$SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO" | base64 | tr -d '\n')" \
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
  --header "Authorization: Basic $(printf '%s' "$SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO" | base64 | tr -d '\n')" \
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
            "encrypt.kek.name": "'"${HCVAULT_KMS_KEY_NAME}"'",
            "encrypt.kms.key.id": "'"${HCVAULT_KMS_KEY_ID}"'",
            "encrypt.kms.type": "'"${HCVAULT_KMS_TYPE}"'"
          },
          "onFailure": "ERROR,NONE"
        }
      ]
    }
  }'
echo

echo "Done."
