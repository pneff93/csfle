# Client-Side Field Level Encryption (CSFLE) with Azure Key Vault

This repository provides a step-by-step demo of the Confluent Cloud feature [Client-Side Field Level Encryption](http://staging-docs-independent.confluent.io/docs-cloud/PR/2843/current/clusters/csfle/overview.html).
As of today, this feature is in Early Access Program.

## Prerequisites

* Confluent Cloud cluster with Advanced Stream Governance package
* For clients, Confluent Platform 7.4.2 or 7.5.1 are required.

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
However, we set up the corresponding configurations to encrypt the `birthday` field.
We then start a consumer with the corresponding configurations to decrypt the field again.

In order to have a realistic scenario, we do not produce and consume via the CLI but develop a
producer and consumer application with Kotlin.

## Create Tag

We first need to create a tag on which we apply the encryption later, such as `PII`.
As of today, we need to create the tag in the Stream Catalog first, see the [documentation](https://docs.confluent.io/platform/current/schema-registry/fundamentals/data-contracts.html#tags) of Data Contracts.

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

We register the schema with setting `PII` to the birthday field and defining the encryption rule

```shell
curl --request POST --url 'https://psrc-abc.westeurope.azure.confluent.cloud/subjects/pneff-csfle-test-value/versions'   \
  --header 'Authorization: Basic <SR API Key>:<SR API Secret>' \ <-- base64 encoded credentials
  --header 'content-type: application/octet-stream' \
  --data '{
            "schemaType": "AVRO",
            "schema": "{  \"name\": \"PersonalData\", \"type\": \"record\", \"namespace\": \"com.csfleExample\", \"fields\": [{\"name\": \"id\", \"type\": \"string\"}, {\"name\": \"name\", \"type\": \"string\"},{\"name\": \"birthday\", \"type\": \"string\", \"confluent:tags\": [ \"PII\"]},{\"name\": \"timestamp\",\"type\": [\"string\", \"null\"]}]}",
            "metadata": {
            "properties": {
            "owner": "Patrick Neff",
            "email": "pneff@confluent.io"
            }
          }
    }' 
```
## Register Rule

```shell
curl --request POST --url 'https://psrc-abc.westeurope.azure.confluent.cloud/subjects/pneff-csfle-test-value/versions'   \
  --header 'Authorization: Basic <SR API Key>:<SR API Secret>' \ <-- base64 encoded credentials
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
           "encrypt.kek.name": "pneff-csfle",
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
  --url 'https://psrc-abc.westeurope.azure.confluent.cloud/subjects/pneff-csfle-test-value/versions/latest'   \
  --header 'Authorization: Basic <SR API Key>:<SR API Secret>' \ <-- base64 encoded credentials | jq
```

or in the CC UI

![](CCEncryptionRule.png)

## Producer configuration

### Gradle
We need to add
```shell
implementation("io.confluent:kafka-avro-serializer:7.4.2")
implementation("io.confluent:kafka-schema-registry-client-encryption-azure:7.4.2")
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

We continuously produce data with the encryption (the topic `pneff-csfle-test` needs to be created before) by executing
```
./gradlew run
```

We can see in the logs that everything is working fine
```shell
[ForkJoinPool.commonPool-worker-1] INFO  com.microsoft.aad.msal4j.AcquireTokenSilentSupplier - Returning token from cache
[ForkJoinPool.commonPool-worker-1] INFO  com.azure.identity.ClientSecretCredential - Azure Identity => getToken() result for scopes [https://vault.azure.net/.default]: SUCCESS
[ForkJoinPool.commonPool-worker-1] INFO  com.azure.core.implementation.AccessTokenCache - Acquired a new access token.
[kafka-producer-network-thread | producer-2] INFO  KafkaProducer - event produced to pneff-csfle-test
```

or check the encrypted field messages in the CC UI

![](CCEvents.png)

## Consumer

We configure the consumer with the corresponding configurations
and just log the consumed event.
We can run it again with
```
./gradlew run
```

It may take a few seconds but then we can see all events with decrypted `birthday`
field:

```shell
[main] INFO  KafkaConsumer - We consumed the event {"id": "0", "name": "Anna", "birthday": "1993-08-01", "timestamp": "2023-10-07T20:48:02.624Z"}
[main] INFO  KafkaConsumer - We consumed the event {"id": "1", "name": "Joe", "birthday": "1996-09-11", "timestamp": "2023-10-07T20:48:18.005Z"}
```
