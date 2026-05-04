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
		"security.protocol": "SASL_SSL",
		"sasl.mechanisms":   "PLAIN",
		"sasl.username":     os.Getenv("KAFKA_SASL_USERNAME"),
		"sasl.password":     os.Getenv("KAFKA_SASL_PASSWORD"),
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
		"security.protocol": "SASL_SSL",
		"sasl.mechanisms":   "PLAIN",
		"sasl.username":     os.Getenv("KAFKA_SASL_USERNAME"),
		"sasl.password":     os.Getenv("KAFKA_SASL_PASSWORD"),
	}, nil
}

// GetAzureRuleConfig returns Azure service-principal credentials packaged for
// the Avro serializer/deserializer RuleConfig. The Confluent Go Azure KMS
// driver reads `tenant.id`, `client.id`, and `client.secret` from this map and
// constructs a ClientSecretCredential. Passing them explicitly is more
// reliable than relying on Azure SDK environment-variable defaults.
func GetAzureRuleConfig() (map[string]string, error) {
	tenant, err := getEnv("AZURE_TENANT_ID")
	if err != nil {
		return nil, err
	}
	clientID, err := getEnv("AZURE_CLIENT_ID")
	if err != nil {
		return nil, err
	}
	secret, err := getEnv("AZURE_CLIENT_SECRET")
	if err != nil {
		return nil, err
	}
	return map[string]string{
		"tenant.id":     tenant,
		"client.id":     clientID,
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
		"KAFKA_SASL_USERNAME",
		"KAFKA_SASL_PASSWORD",
		"SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO",
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
