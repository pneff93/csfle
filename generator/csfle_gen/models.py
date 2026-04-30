import random
from typing import Literal

from pydantic import BaseModel, Field, model_validator


Target = Literal["cloud", "platform"]
Kms = Literal["aws", "azure", "gcp", "hashicorp"]
Language = Literal["python", "java"]


def _random_uid() -> str:
    """Four-digit zero-padded uniquifier so generations don't collide on Kafka topic,
    consumer group, or Schema Registry KEK name when run against the same cluster."""
    return f"{random.randint(0, 9999):04d}"


class KafkaConfig(BaseModel):
    bootstrap_servers: str
    sasl_username: str | None = None
    sasl_password: str | None = None


class SrConfig(BaseModel):
    url: str
    basic_auth_user_info: str | None = None


class GenerationConfig(BaseModel):
    project_name: str
    description: str = ""
    language: Language = "python"
    target: Target
    kms: Kms
    kafka: KafkaConfig
    schema_registry: SrConfig
    kms_params: dict[str, str | None] = Field(default_factory=dict)

    uid: str = Field(default_factory=_random_uid)
    topic: str = ""        # derived: <project_name>-<uid>
    group_id: str = ""     # derived: <project_name>-<uid>-consumer-group
    kek_name: str = ""     # derived: <project_name>-<uid>-kek
    auto_offset_reset: str = "earliest"
    confluent_kafka_version: str = "2.12.2"
    python_min_version: str = "3.8"
    java_version: str = "17"
    confluent_java_version: str = "7.9.4"
    kafka_clients_version: str = "3.9.1"
    avro_version: str = "1.12.1"

    @model_validator(mode="after")
    def _derive_unique_names(self) -> "GenerationConfig":
        if not self.uid:
            self.uid = _random_uid()
        prefix = f"{self.project_name}-{self.uid}"
        if not self.topic:
            self.topic = prefix
        if not self.group_id:
            self.group_id = f"{prefix}-consumer-group"
        if not self.kek_name:
            self.kek_name = f"{prefix}-kek"
        return self
