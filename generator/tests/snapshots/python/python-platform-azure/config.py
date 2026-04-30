"""Configuration module for CSFLE demo with Confluent Platform.

Loads configuration from environment variables using python-dotenv.
Create a .env file based on .env.example to configure the application.
"""

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')


def _get_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(
            f"Missing required configuration: {var_name}\n"
            f"Please create a .env file based on .env.example"
        )
    return value


def get_topic() -> str:
    return _get_env('KAFKA_TOPIC')


def get_schema_registry_config() -> Dict[str, str]:
    return {
        'url': _get_env('SCHEMA_REGISTRY_URL')
    }


def get_producer_config() -> Dict[str, str]:
    return {
        'bootstrap.servers': _get_env('KAFKA_BOOTSTRAP_SERVERS')
    }


def get_consumer_config() -> Dict[str, str]:
    return {
        'bootstrap.servers': _get_env('KAFKA_BOOTSTRAP_SERVERS'),
        'group.id': _get_env('KAFKA_GROUP_ID'),
        'auto.offset.reset': _get_env('KAFKA_AUTO_OFFSET_RESET')
    }


def validate_config():
    """Validate all required configuration variables are set."""
    _get_env('KAFKA_TOPIC')
    _get_env('KAFKA_GROUP_ID')
    _get_env('KAFKA_AUTO_OFFSET_RESET')
    _get_env('KAFKA_BOOTSTRAP_SERVERS')
    _get_env('SCHEMA_REGISTRY_URL')
    _get_env('AZURE_KMS_KEY_NAME')
    _get_env('AZURE_KMS_TYPE')
    _get_env('AZURE_KMS_KEY_ID')
    _get_env('AZURE_TENANT_ID')
    _get_env('AZURE_CLIENT_ID')
    _get_env('AZURE_CLIENT_SECRET')
