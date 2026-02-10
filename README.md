# Client-Side Field Level Encryption (CSFLE) & Client-Side Payload Encryption (CSPE)

This repository provides several demos of the Confluent Cloud
feature [Client-Side Field Level Encryption](https://docs.confluent.io/cloud/current/clusters/csfle/overview.html) as
well as
[Client-Side Payload Encryption](https://docs.confluent.io/cloud/current/security/encrypt/cspe.html).

## Confluent Cloud Examples

Step-by-step guidelines for different KMS integrations with Confluent Cloud:

| **Scenario**                                                  | **Key Vault**              | **Encryption type** | **KEK shared** |
|---------------------------------------------------------------|----------------------------|---------------------|----------------|
| [Azure - Kotlin](confluent_cloud/azure/kotlin/README.md)      | Azure Key Vault            | CSFLE               | no             |
| [Azure - Python](confluent_cloud/azure/python/README.md)      | Azure Key Vault            | CSFLE               | no             |
| [HashiCorp](confluent_cloud/hashicorp/README.md)              | HashiCorp Vault            | CSFLE               | no             |
| [AWS - Kotlin](confluent_cloud/aws/kotlin/README.md)          | AWS Key Management Service | CSFLE               | no             |
| [AWS - Python](confluent_cloud/aws/python/README.md)          | AWS Key Management Service | CSFLE               | no             |
| [GCP](confluent_cloud/gcp/README.md)                          | GCP Key Management Service | CSFLE               | no             |
| [AWS - Shared](confluent_cloud/aws_shared_kek/README.md)      | AWS Key Management Service | CSFLE               | yes            |
| [Azure - SM Connect](confluent_cloud/azure_connect/README.md) | Azure Key Vault            | CSFLE               | no             |
| [Azure - CSPE](confluent_cloud/azure_cspe/README.md)          | Azure Key Vault            | CSPE                | no             |

## Confluent Platform Examples

Step-by-step guidelines for different KMS integrations with Confluent Platform:

| **Scenario**                                            | **Key Vault**              | **Encryption type** | **KEK shared** |
|---------------------------------------------------------|----------------------------|---------------------|----------------|
| [AWS - Java](confluent_platform/aws/java/README.md)     | AWS Key Management Service | CSFLE               | no             |
| [AWS - Python](confluent_platform/aws/python/README.md) | AWS Key Management Service | CSFLE               | no             |

## Prerequisites

* Confluent Cloud cluster with Advanced Stream Governance package
* For clients, Confluent Platform 7.4.2 or 7.5.1 are required.

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
