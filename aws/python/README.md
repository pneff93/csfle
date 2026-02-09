# Client-Side Field Level Encryption (CSFLE) with AWS KMS

This repository provides a step-by-step demo of the Confluent Cloud
feature [Client-Side Field Level Encryption](https://docs.confluent.io/cloud/current/clusters/csfle/overview.html).

## Prerequisites

* Confluent Cloud cluster with Advanced Stream Governance package
* For the support python client versions see the
  requirements [here](https://docs.confluent.io/cloud/current/security/encrypt/csfle/client-side.html#confluent-python-client-for-ak)

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

To have a realistic scenario, we do not produce and consume via the CLI but develop a
producer and consumer application with Python.

## Environment

```aiignore shell
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## AWS

In the KMS section of the AWS Management Console, create a new Symmetric Key with Encrypt/Decrypt configuration

![](../images/aws_create_key.jpg)

![](../images/aws_key_config.jpg)

As you click through this process you will be asked to define `Admins` and `Users` for your key. Ensure you grant access
to the `User` that you want use in your Producer/Consumer app.

![](../images/aws_key_users.jpg)

### AWS IAM

After your Key has been created, navigate to AWS IAM and create an Access Key for the User that you granted permissions
to in the previous step.

![](../images/aws_create_access_key.jpg)

:warning: **Important:** Ensure you copy your Access Key ID and Secret (or download the csv file) :warning:

## Register the tag

We first need to create a tag on which we apply the encryption later, such as `PII`.
As of today, we need to create the tag in the Stream Catalog first, see
the [documentation](https://docs.confluent.io/platform/current/schema-registry/fundamentals/data-contracts.html#tags) of
Data Contracts.

Go to Confluent Cloud UI. From there select your environment and navigate to Catalog Management from the left side menu.
`Home > Environments > [Your-Environment] > Stream Governance > Catalog management > Tags > Create Tags > PII`

## Register Schema

We register the schema with setting `PII` to the birthday field and defining the encryption rule

```shell
curl --location '<BOOTSTRAP_SERVERS_URL>/subjects/csfle-demo-value/versions' \
--header 'Accept: application/vnd.schemaregistry.v1+json' \
--header 'Content-Type: application/json' \
--header 'Authorization: Basic <base64 encoded SR_KEY:SR_SECRET>' \
--data '{
    "schemaType": "AVRO",
    "schema": "{  \"name\": \"PersonalData\", \"type\": \"record\", \"namespace\": \"com.csfleExample\", \"fields\": [{\"name\": \"id\", \"type\": \"string\"}, {\"name\": \"name\", \"type\": \"string\"},{\"name\": \"birthday\", \"type\": \"string\", \"confluent:tags\": [ \"PII\"]},{\"name\": \"timestamp\",\"type\": [\"string\", \"null\"]}]}"
}'
```

## Register Rule

```shell
curl --location 'BOOTSTRAP_SERVERS_URL/subjects/csfle-demo-value/versions' \
--header 'Accept: application/vnd.schemaregistry.v1+json' \
--header 'Content-Type: application/json' \
--header 'Authorization: Basic <base64 encoded SR_KEY:SR_SECRET>' \
--data '{
    "ruleSet": {
        "domainRules": [
            {
                "name": "encryptPII",
                "kind": "TRANSFORM",
                "type": "ENCRYPT",
                "mode": "WRITEREAD",
                "tags": [
                    "PII"
                ],
                "params": {
                    "encrypt.kek.name": "<AWS KMS Key name>",
                    "encrypt.kms.key.id": "<AWS KMS Key ARN>",
                    "encrypt.kms.type": "aws-kms"
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
  --url '<SR_URL>/subjects/csfle-demo-value/versions/latest'   \
  --header 'Authorization: Basic <base64 encoded SR_API_KEY>:<SR_API_SECRET>' | jq
```

or in the CC UI (the name of schema subject would be csfle-demo)

![](../CCEncryptionRule.png)

## Client configuration

We need to adjust the [producer](avro_producer.py)'s and [consumer](avro_consumer.py)'s configuration.

You need to have the following information

* Broker URL
* Kafka API Key
* Kafka API Secret
* Schema Registry URL
* Schema Registry API Key
* Schema Registry API Secret
* ARN of the key you created in AWS
* AWS Credentials: Access Key ID & Secret Access Key

Update the corresponding variables in each client.

## Execute

Run the producer

```aiignore python
python avro_producer.py
```

In the logs you should see

```log
PersonalData record b'2' successfully produced to csfle-demo [1] at offset 0
```

Now you can consume the data

```pycon
python avro_consumer.py
```

In the logs you can see

```log
--- Personal Data ---
  ID:        19
  Name:      Anna
  Birthday:  2006-12-12
  Timestamp: 2025-12-12T15:11:42.477591+00:00
---------------------
```

You can simulate a scenario where a client without access to the KEK consumes the sensitive data.
Change the Client Secret string, e.g. add a character at the end, so that authentication fails.

You will see some errors in the logs, but you will also see the following

```log
--- Personal Data ---
  ID:        2
  Name:      Anna
  Birthday:  yabvlkT//S+QDAXP7idIl3wU3pHR8/2oZZA8ORovepAun1eLORo=
  Timestamp: 2025-12-12T15:11:42.476313+00:00
---------------------
```

Consumers without access to the KEK are not able to read the fields that you have encrypted with CSFLE.
