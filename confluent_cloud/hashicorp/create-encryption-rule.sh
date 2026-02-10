curl --request POST --url "${SR_REST_ENDPOINT}/subjects/${TOPIC}-value/versions" \
  --user "${SR_API_KEY}:${SR_API_SECRET}" \
  --header 'Content-Type: application/vnd.schemaregistry.v1+json' \
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
           "encrypt.kek.name": "csfle",
           "encrypt.kms.key.id": "http://127.0.0.1:8200/transit/keys/csfle",
           "encrypt.kms.type": "hcvault",
           "encrypt.dek.expiry.days": 1
          },
        "onFailure": "ERROR,NONE"
        }
        ]
      } 
    }'
