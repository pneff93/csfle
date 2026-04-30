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
	"strings"

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

// GetGcpRuleConfig returns Google Cloud service-account credentials packaged
// for the Avro serializer/deserializer RuleConfig. The Confluent Go GCP KMS
// driver reads `client.id`, `client.email`, `private.key.id`, and
// `private.key` from this map.
//
// godotenv preserves the literal `\n` escapes inside the double-quoted PEM,
// so we unescape them here before handing the key to the driver.
func GetGcpRuleConfig() (map[string]string, error) {
	clientID, err := getEnv("GCP_CLIENT_ID")
	if err != nil {
		return nil, err
	}
	clientEmail, err := getEnv("GCP_CLIENT_EMAIL")
	if err != nil {
		return nil, err
	}
	privateKeyID, err := getEnv("GCP_PRIVATE_KEY_ID")
	if err != nil {
		return nil, err
	}
	privateKey, err := getEnv("GCP_PRIVATE_KEY")
	if err != nil {
		return nil, err
	}
	return map[string]string{
		"client.id":      clientID,
		"client.email":   clientEmail,
		"private.key.id": privateKeyID,
		"private.key":    strings.ReplaceAll(privateKey, "\\n", "\n"),
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
		"GCP_KMS_KEY_NAME",
		"GCP_KMS_TYPE",
		"GCP_KMS_KEY_ID",
		"GCP_CLIENT_ID",
		"GCP_CLIENT_EMAIL",
		"GCP_PRIVATE_KEY_ID",
		"GCP_PRIVATE_KEY",
	}
	for _, name := range required {
		if _, err := getEnv(name); err != nil {
			return err
		}
	}
	return nil
}
