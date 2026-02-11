# Client-Side Field Level Encryption (CSFLE) & Client-Side Payload Encryption (CSPE)

This repository provides several demos of the Confluent Cloud
feature [Client-Side Field Level Encryption](https://docs.confluent.io/cloud/current/clusters/csfle/overview.html) as
well as
[Client-Side Payload Encryption](https://docs.confluent.io/cloud/current/security/encrypt/cspe.html).

## Confluent Cloud Examples

Step-by-step guidelines for different KMS integrations with Confluent Cloud:

| **Scenario**                                                | **Client**    | **Key Vault**              | **Encryption type** | **KEK shared** |
|-------------------------------------------------------------|---------------|----------------------------|---------------------|----------------|
| [AWS](confluent_cloud/aws/kotlin/README.md)                 | Kotlin        | AWS Key Management Service | CSFLE               | no             |
| [AWS](confluent_cloud/aws/python/README.md)                 | Python        | AWS Key Management Service | CSFLE               | no             |
| [AWS Shared KEK](confluent_cloud/aws_shared_kek/README.md)  | Kotlin        | AWS Key Management Service | CSFLE               | yes            |
| [Azure](confluent_cloud/azure/kotlin/README.md)             | Kotlin        | Azure Key Vault            | CSFLE               | no             |
| [Azure](confluent_cloud/azure/python/README.md)             | Python        | Azure Key Vault            | CSFLE               | no             |
| [Azure CSPE](confluent_cloud/azure_cspe/README.md)          | Kotlin        | Azure Key Vault            | CSPE                | no             |
| [Azure SM Connect](confluent_cloud/azure_connect/README.md) | Kafka Connect | Azure Key Vault            | CSFLE               | no             |
| [HashiCorp](confluent_cloud/hashicorp/README.md)            | Kotlin        | HashiCorp Vault            | CSFLE               | no             |
| [GCP](confluent_cloud/gcp/README.md)                        | Kotlin        | GCP Key Management Service | CSFLE               | no             |

## Confluent Platform Examples

Step-by-step guidelines for different KMS integrations with Confluent Platform:

| **Scenario**                                            | **Client** | **Key Vault**              | **Encryption type** | **KEK shared** |
|---------------------------------------------------------|------------|----------------------------|---------------------|----------------|
| [AWS](confluent_platform/aws/java/README.md)            | Java       | AWS Key Management Service | CSFLE               | no             |
| [AWS](confluent_platform/aws/python/README.md)          | Python     | AWS Key Management Service | CSFLE               | no             |
| [Azure](confluent_platform/azure/python/README.md)      | Python     | Azure Key Vault            | CSFLE               | no             |

## Prerequisites

* Confluent Cloud cluster with Advanced Stream Governance package
* To use CSFLE with Confluent Platform in a **production** cluster you have to use Confluent Platform 8.0 or later.
  * Confluent Platform 7.9 introduces CSFLE as an Early Access feature. 7.9 is not supported for production workloads.
* For clients, Confluent Platform 7.4.2 or 7.5.1 are required

## Goal

We will produce personal data to Confluent Cloud in the following form

```json
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
