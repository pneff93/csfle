# Confluent Platform CSFLE Examples

This directory contains the infrastructure needed to test Client-Side Field Level Encryption (CSFLE) with Confluent Platform.

## Setup

The `compose.yml` file sets up a local Confluent Platform environment with the following components:

- **Kafka Broker**
- - Running in KRaft mode (combined controller and broker - **not** supported for production)
- **Schema Registry**
- **Control Center**

This infrastructure enables testing of Client-Side Field Level Encryption with different Key Management Service (KMS) providers.
