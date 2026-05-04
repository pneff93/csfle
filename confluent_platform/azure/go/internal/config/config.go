// Package config loads CSFLE demo configuration from a shared .env file.
//
// The .env file lives in confluent_platform/azure/.env and is shared with the
// Python client. Variables already exported in the shell take precedence over
// values in the .env file (godotenv is non-destructive), so the
// `export AZURE_CLIENT_SECRET=invalid_secret_key` trick in the README works.
package config

import (
	"fmt"
	"os"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/joho/godotenv"
)

func init() {
	for _, path := range []string{"../.env", "../../.env", ".env"} {
		if err := godotenv.Load(path); err == nil {
			return
		}
	}
}

func getEnv(name string) (string, error) {
	v := os.Getenv(name)
	if v == "" {
		return "", fmt.Errorf(
			"missing required configuration: %s\n"+
				"Please set it in ../.env (see ../.env.example)", name)
	}
	return v, nil
}

func GetTopic() (string, error) {
	return getEnv("KAFKA_TOPIC")
}

func GetSchemaRegistryURL() (string, error) {
	return getEnv("SCHEMA_REGISTRY_URL")
}

func GetProducerConfig() (*kafka.ConfigMap, error) {
	bs, err := getEnv("KAFKA_BOOTSTRAP_SERVERS")
	if err != nil {
		return nil, err
	}
	return &kafka.ConfigMap{"bootstrap.servers": bs}, nil
}

func GetConsumerConfig() (*kafka.ConfigMap, error) {
	bs, err := getEnv("KAFKA_BOOTSTRAP_SERVERS")
	if err != nil {
		return nil, err
	}
	group, err := getEnv("KAFKA_GROUP_ID")
	if err != nil {
		return nil, err
	}
	offset, err := getEnv("KAFKA_AUTO_OFFSET_RESET")
	if err != nil {
		return nil, err
	}
	return &kafka.ConfigMap{
		"bootstrap.servers": bs,
		"group.id":          group,
		"auto.offset.reset": offset,
	}, nil
}

// GetAzureRuleConfig returns Azure service-principal credentials packaged for
// the Avro serializer/deserializer RuleConfig. The Confluent Go Azure KMS
// driver reads `tenant.id`, `client.id`, and `client.secret` from this config
// and constructs a ClientSecretCredential. Passing them explicitly is more
// reliable than relying on Azure SDK environment-variable defaults.
func GetAzureRuleConfig() (map[string]string, error) {
	tenant, err := getEnv("AZURE_TENANT_ID")
	if err != nil {
		return nil, err
	}
	client, err := getEnv("AZURE_CLIENT_ID")
	if err != nil {
		return nil, err
	}
	secret, err := getEnv("AZURE_CLIENT_SECRET")
	if err != nil {
		return nil, err
	}
	return map[string]string{
		"tenant.id":     tenant,
		"client.id":     client,
		"client.secret": secret,
	}, nil
}

func Validate() error {
	required := []string{
		"KAFKA_TOPIC",
		"KAFKA_BOOTSTRAP_SERVERS",
		"KAFKA_GROUP_ID",
		"KAFKA_AUTO_OFFSET_RESET",
		"SCHEMA_REGISTRY_URL",
		"AZURE_KMS_KEY_NAME",
		"AZURE_KMS_TYPE",
		"AZURE_KMS_KEY_ID",
		"AZURE_TENANT_ID",
		"AZURE_CLIENT_ID",
		"AZURE_CLIENT_SECRET",
	}
	for _, name := range required {
		if _, err := getEnv(name); err != nil {
			return err
		}
	}
	return nil
}
