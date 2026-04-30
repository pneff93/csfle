// Package config loads CSFLE demo configuration from this project's .env file.
//
// godotenv is non-clobbering: variables already exported in the shell take
// precedence over values in .env. That's what makes the unauthorized-access
// trick in the README (`export <KMS_CRED>=invalid`) work for testing
// decryption failures.
package config

import (
	"fmt"
	"os"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/joho/godotenv"
)

func init() {
	// Try a few candidate paths so the binary works whether you run it from
	// the project root, from cmd/producer, or from a built binary in bin/.
	for _, path := range []string{".env", "../.env", "../../.env", "../../../.env"} {
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
				"Please set it in .env (see .env.example)", name)
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
	return &kafka.ConfigMap{
		"bootstrap.servers": bs,
	}, nil
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

// GetHcVaultRuleConfig returns the HashiCorp Vault token packaged for the Avro
// serializer/deserializer RuleConfig. The Confluent Go hcvault driver reads
// `token.id` from this map.
func GetHcVaultRuleConfig() (map[string]string, error) {
	token, err := getEnv("VAULT_TOKEN")
	if err != nil {
		return nil, err
	}
	return map[string]string{
		"token.id": token,
	}, nil
}

func Validate() error {
	required := []string{
		"KAFKA_TOPIC",
		"KAFKA_BOOTSTRAP_SERVERS",
		"KAFKA_GROUP_ID",
		"KAFKA_AUTO_OFFSET_RESET",
		"SCHEMA_REGISTRY_URL",
		"HCVAULT_KMS_KEY_NAME",
		"HCVAULT_KMS_TYPE",
		"HCVAULT_KMS_KEY_ID",
		"VAULT_ADDR",
		"VAULT_TOKEN",
	}
	for _, name := range required {
		if _, err := getEnv(name); err != nil {
			return err
		}
	}
	return nil
}
