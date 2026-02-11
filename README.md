# 🔐 Client-Side Field Level Encryption (CSFLE) & Client-Side Payload Encryption (CSPE)

This repository provides demos for implementing **Client-Side Field Level Encryption (CSFLE)** and **Client-Side Payload Encryption (CSPE)** with Confluent Cloud and Confluent Platform.

Encrypt sensitive data at the source before it ever reaches Kafka, ensuring end-to-end data protection and compliance with privacy regulations like GDPR, HIPAA, and CCPA.

> This repository is intended for demonstration purposes only. If you plan to use it in production, you must review and strengthen the security practices accordingly.

---

## ☁️ Confluent Cloud Examples

Step-by-step guidelines for different KMS integrations with Confluent Cloud:

| **Scenario**                                                | **Client**    | **Key Vault**              | **Encryption Type** | **KEK Shared** |
|-------------------------------------------------------------|---------------|----------------------------|---------------------|----------------|
| [AWS](confluent_cloud/aws/kotlin/README.md)                 | Kotlin        | AWS Key Management Service | CSFLE               | ❌             |
| [AWS](confluent_cloud/aws/python/README.md)                 | Python        | AWS Key Management Service | CSFLE               | ❌             |
| [AWS Shared KEK](confluent_cloud/aws_shared_kek/README.md)  | Kotlin        | AWS Key Management Service | CSFLE               | ✅             |
| [Azure](confluent_cloud/azure/kotlin/README.md)             | Kotlin        | Azure Key Vault            | CSFLE               | ❌             |
| [Azure](confluent_cloud/azure/python/README.md)             | Python        | Azure Key Vault            | CSFLE               | ❌             |
| [Azure CSPE](confluent_cloud/azure_cspe/README.md)          | Kotlin        | Azure Key Vault            | CSPE                | ❌             |
| [Azure SM Connect](confluent_cloud/azure_connect/README.md) | Kafka Connect | Azure Key Vault            | CSFLE               | ❌             |
| [HashiCorp](confluent_cloud/hashicorp/README.md)            | Kotlin        | HashiCorp Vault            | CSFLE               | ❌             |
| [GCP](confluent_cloud/gcp/README.md)                        | Kotlin        | GCP Key Management Service | CSFLE               | ❌             |

---

## 🖥️ Confluent Platform Examples

Step-by-step guidelines for different KMS integrations with Confluent Platform:

| **Scenario**                                            | **Client** | **Key Vault**              | **Encryption Type** | **KEK Shared** |
|---------------------------------------------------------|------------|----------------------------|---------------------|----------------|
| [AWS](confluent_platform/aws/java/README.md)            | Java       | AWS Key Management Service | CSFLE               | ❌             |
| [AWS](confluent_platform/aws/python/README.md)          | Python     | AWS Key Management Service | CSFLE               | ❌             |
| [Azure](confluent_platform/azure/python/README.md)      | Python     | Azure Key Vault            | CSFLE               | ❌             |

---

## 📋 Prerequisites

* ✅ Confluent Cloud cluster with **Advanced Stream Governance** package
* ✅ To use CSFLE with Confluent Platform in a **production** cluster, you must use **Confluent Platform 8.0 or later**
  * ⚠️ Confluent Platform 7.9 introduces CSFLE already but as an Early Access feature and is **not supported for production workloads**
* ✅ For clients, **Confluent Platform 7.4.2 or 7.5.1** are required

---

## 🎯 Goal

This demo shows how to protect sensitive personal data by encrypting specific fields before they're sent to Kafka.

### Example Scenario

We produce personal data to Confluent Cloud/Confluent Platform in the following form:

```json
{
  "id": "0",
  "name": "Anna",
  "birthday": "1993-08-01",
  "timestamp": "2023-10-07T19:54:21.884Z"
}
```

**The `birthday` field is automatically encrypted** using CSFLE before being sent to Kafka. When a consumer reads the data with the proper decryption configuration, the field is seamlessly decrypted.

### Implementation

To demonstrate a realistic use case, we build complete producer and consumer applications (not just CLI commands) using modern programming languages like Kotlin, Python, and Java.

---

## 📚 Official Documentation & Resources

### Client-Side Field Level Encryption (CSFLE)

* **Confluent Cloud:** [CSFLE Documentation](https://docs.confluent.io/cloud/current/clusters/csfle/overview.html)
* **Confluent Platform:** [CSFLE Documentation](https://docs.confluent.io/platform/current/security/protect-data/csfle/overview.html)

### Client-Side Payload Encryption (CSPE)

* **Confluent Cloud:** [CSPE Documentation](https://docs.confluent.io/cloud/current/security/encrypt/cspe.html)
* **Confluent Platform**: [CSPE Documentation](https://docs.confluent.io/platform/current/security/protect-data/cspe.html)

---

**Need help?** Visit the [Confluent Community](https://forum.confluent.io/) or check out the [Confluent Cloud Support](https://support.confluent.io/).
