"""Configuration module for CSFLE demo.

Loads configuration from environment variables using python-dotenv.
Create a .env file based on .env.example to configure the application.
"""

import os
from pathlib import Path
from typing import Dict, Tuple
from dotenv import load_dotenv

# Load .env file from the same directory as this config module
load_dotenv(Path(__file__).parent / '.env')


def _get_env(var_name: str, required: bool = True, default: str = None) -> str:
    """Get an environment variable with validation.

    Args:
        var_name: Name of the environment variable
        required: Whether the variable is required
        default: Default value if not required and not set

    Returns:
        The environment variable value

    Raises:
        ValueError: If a required variable is not set
    """
    value = os.getenv(var_name, default)
    if required and value is None:
        raise ValueError(
            f"Missing required configuration: {var_name}\n"
            f"Please create a .env file based on .env.example"
        )
    return value


def get_topic() -> str:
    """Get the Kafka topic name.

    Returns:
        Topic name
    """
    return _get_env('KAFKA_TOPIC', required=True)


def get_schema_registry_config() -> Dict[str, str]:
    """Get Schema Registry client configuration.

    Returns:
        Dictionary with 'url' and 'basic.auth.user.info' keys
    """
    return {
        'url': _get_env('SCHEMA_REGISTRY_URL'),
        'basic.auth.user.info': _get_env('SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO')
    }


def get_producer_config() -> Dict[str, str]:
    """Get Kafka producer configuration.

    Returns:
        Dictionary with producer configuration
    """
    return {
        'bootstrap.servers': _get_env('KAFKA_BOOTSTRAP_SERVERS'),
        'sasl.mechanisms': 'PLAIN',
        'security.protocol': 'SASL_SSL',
        'sasl.username': _get_env('KAFKA_SASL_USERNAME'),
        'sasl.password': _get_env('KAFKA_SASL_PASSWORD')
    }


def get_consumer_config() -> Dict[str, str]:
    """Get Kafka consumer configuration.

    Returns:
        Dictionary with consumer configuration
    """
    return {
        'bootstrap.servers': _get_env('KAFKA_BOOTSTRAP_SERVERS'),
        'sasl.mechanisms': 'PLAIN',
        'security.protocol': 'SASL_SSL',
        'sasl.username': _get_env('KAFKA_SASL_USERNAME'),
        'sasl.password': _get_env('KAFKA_SASL_PASSWORD'),
        'group.id': _get_env('KAFKA_GROUP_ID'),
        'auto.offset.reset': _get_env('KAFKA_AUTO_OFFSET_RESET')
    }


def get_kms_config() -> Tuple[str, str, str]:
    """Get AWS KMS configuration for the producer.

    Returns:
        Tuple of (kek_name, kms_type, kms_key_id)
    """
    kek_name = _get_env('AWS_KMS_KEY_NAME')
    kms_type = _get_env('AWS_KMS_TYPE')
    kms_key_id = _get_env('AWS_KMS_KEY_ID')

    return kek_name, kms_type, kms_key_id


def validate_config():
    """Validate that all required configuration is present.

    This function attempts to load all required configuration values.
    It will raise a ValueError if any required values are missing.

    Raises:
        ValueError: If any required configuration is missing
    """
    # Validate Kafka configuration
    _get_env('KAFKA_TOPIC')
    _get_env('KAFKA_BOOTSTRAP_SERVERS')
    _get_env('KAFKA_SASL_USERNAME')
    _get_env('KAFKA_SASL_PASSWORD')
    _get_env('KAFKA_GROUP_ID')
    _get_env('KAFKA_AUTO_OFFSET_RESET')

    # Validate Schema Registry configuration
    _get_env('SCHEMA_REGISTRY_URL')
    _get_env('SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO')

    # Validate AWS KMS configuration
    _get_env('AWS_KMS_KEY_NAME')
    _get_env('AWS_KMS_TYPE')
    _get_env('AWS_KMS_KEY_ID')

    # Validate AWS credentials (using standard AWS SDK environment variable names)
    _get_env('AWS_ACCESS_KEY_ID')
    _get_env('AWS_SECRET_ACCESS_KEY')
