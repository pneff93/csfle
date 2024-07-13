# Client-Side Field Level Encryption (CSFLE)

This repository provides several demos of the Confluent Cloud feature [Client-Side Field Level Encryption](https://docs.confluent.io/cloud/current/clusters/csfle/overview.html).


It covers step-by-step guidelines for different KMS via folders:
| **Scenario**                                   | **Key Vault**              | **KEK shared** |
|------------------------------------------------|----------------------------|----------------|
| [Azure](azure/README.md)                       | Azure Key Vault            | no             |
| [HashiCorp](hashicorp/README.md)               | HashiCorp Vault            | no             |
| [AWS](aws/README.md)                           | AWS Key Management Service | no             |
| [GCP](gcp/README.md)                           | GCP Key Management Service | no             |
| [AWS - Shared](aws_shared_kek/README.md) | AWS Key Management Service | yes            |

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
