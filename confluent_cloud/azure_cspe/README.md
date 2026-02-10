# Client-Side Payload Encryption (CSPE) with Azure Key Vault

This repository provides a step-by-step demo of the Confluent Cloud feature [Client-Side Payload Encryption](https://docs.confluent.io/cloud/current/security/encrypt/cspe.html).

## Prerequisites

* Confluent Cloud cluster with Advanced Stream Governance package

## Goal

We will produce personal data to Confluent Cloud in the following form 
```
{
    "id": "0",
    "name": "Anna",
    "birthday": "1993-08-01",
    "timestamp": "2023-10-07T19:54:21.884Z"
}
```
However, we set up the corresponding configurations to encrypt the entire payload.
We then start a consumer with the corresponding configurations to decrypt the payload again.

In order to have a realistic scenario, we do not produce and consume via the CLI but develop a
producer and consumer application with Kotlin.

## Azure Key Vault

### Azure App registration

In Azure AD (Entra ID), we create an app with a secret, see this [Quickstart documentation](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app).
Copy the
* tenant ID
* client ID
* secret value (you need to copy it directly after creation)

### Azure Key Vault

Create a Key Vault and a key. Copy the Key Identifier as displayed below

![](AzureKey.png)

### Azure Assign a Key Vault access policy

In the Key Vault, we use Access policies to grant permission for the key to the registered application, see the [documentation](https://learn.microsoft.com/en-us/azure/key-vault/general/assign-access-policy?tabs=azure-portal).
We provide "All Key Permissions" (in production we recommend following the principle of least privilege).

![](AzureKeyAccess.png)

## Register Schema

We register the schema defining the encryption rule

```shell
curl --request POST --url 'https://psrc-abc.westeurope.azure.confluent.cloud/subjects/pneff-cspe-test-value/versions'   \
  --header 'Authorization: Basic <SR API Key>:<SR API Secret>' \ <-- base64 encoded credentials
  --header 'content-type: application/json' \
  --data '{
            "schemaType": "AVRO",
            "schema": "{  \"name\": \"PersonalData\", \"type\": \"record\", \"namespace\": \"com.cspeExample\", \"fields\": [{\"name\": \"id\", \"type\": \"string\"}, {\"name\": \"name\", \"type\": \"string\"},{\"name\": \"birthday\", \"type\": \"string\"},{\"name\": \"timestamp\",\"type\": [\"string\", \"null\"]}]}",
            "metadata": {
            "properties": {
            "owner": "Patrick Neff",
            "email": "pneff@confluent.io"
            }
          }
    }' 
```
## Register Rule

Be aware, that for CSPE you need to configure `encodingRules`.

```shell
curl --request POST --url 'https://psrc-abc.westeurope.azure.confluent.cloud/subjects/pneff-cspe-test-value/versions'   \
  --header 'Authorization: Basic <SR API Key>:<SR API Secret>' \ <-- base64 encoded credentials
  --header 'Content-Type: application/vnd.schemaregistry.v1+json' \
  --data '{
        "ruleSet": {
        "encodingRules": [
      {
        "name": "encryptPayload",
        "kind": "TRANSFORM",
        "type": "ENCRYPT_PAYLOAD",
        "mode": "WRITEREAD",
        "params": {
           "encrypt.kek.name": "pneff-cspe",
           "encrypt.kms.key.id": "<Azure Key Identifier>",
           "encrypt.kms.type": "azure-kms"
          },
        "onFailure": "ERROR,NONE"
        }
        ]
      } 
    }'
```

We can check that everything is registered correctly by either executing
```shell
curl --request GET \
  --url 'https://psrc-abc.westeurope.azure.confluent.cloud/subjects/pneff-cspe-test-value/versions/latest'   \
  --header 'Authorization: Basic <SR API Key>:<SR API Secret>' \ <-- base64 encoded credentials | jq
```

## Producer configuration

### Gradle
We need to add
```shell
implementation("io.confluent:kafka-avro-serializer:8.1.0")
implementation("io.confluent:kafka-schema-registry-client-encryption-azure:8.1.0")
```

### Producer
We need to adjust the configuration by adding
```kotlin
// Encryption
settings.setProperty("rule.executors._default_.param.tenant.id", "<tenant ID>")
settings.setProperty("rule.executors._default_.param.client.id", "<client ID>")
settings.setProperty("rule.executors._default_.param.client.secret", "<secret value>")

// Required since we manually create schemas
settings.setProperty("use.latest.version", "true")
settings.setProperty("auto.register.schemas","false")
```

We continuously produce data with the encryption (the topic `pneff-cspe-test` needs to be created before) by executing
```
./gradlew run
```

We can see in the logs that everything is working fine
```shell
[ForkJoinPool.commonPool-worker-1] INFO  com.microsoft.aad.msal4j.AcquireTokenSilentSupplier - Returning token from cache
[ForkJoinPool.commonPool-worker-1] INFO  com.azure.identity.ClientSecretCredential - Azure Identity => getToken() result for scopes [https://vault.azure.net/.default]: SUCCESS
[ForkJoinPool.commonPool-worker-1] INFO  com.azure.core.implementation.AccessTokenCache - Acquired a new access token.
[kafka-producer-network-thread | producer-2] INFO  KafkaProducer - event produced to pneff-cspe-test
```

## Consumer

We configure the consumer with the corresponding configurations
and just log the consumed event.
We can run it again with
```
./gradlew run
```

It may take a few seconds but then we can see all events with decrypted payload:

```shell
[main] INFO  KafkaConsumer - We consumed the event {"id": "0", "name": "Anna", "birthday": "1993-08-01", "timestamp": "2023-10-07T20:48:02.624Z"}
[main] INFO  KafkaConsumer - We consumed the event {"id": "1", "name": "Joe", "birthday": "1996-09-11", "timestamp": "2023-10-07T20:48:18.005Z"}
```

If we do not provide KMS access configuration we receive the Exception `Failed to decrypt with all KEKs`.
