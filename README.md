# Client-Side Field Level Encryption (CSFLE)

This repository provides several demos of the Confluent Cloud feature [Client-Side Field Level Encryption](http://staging-docs-independent.confluent.io/docs-cloud/PR/2843/current/clusters/csfle/overview.html).
As of today, this feature is in Early Access Program.

It covers step-by-step guidelines for different KMS via branches:
- [x] [Azure Key Vault](https://github.com/pneff93/csfle/tree/azure)
- [x] [HashiCorp Vault](https://github.com/pneff93/csfle/tree/hashicorp)
- [ ] AWS Secrets Manager
- [x] [GCP KMS](https://github.com/pneff93/csfle/tree/gcp)

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
