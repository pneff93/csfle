package main

import (
	"fmt"
	"os"
	"time"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/confluentinc/confluent-kafka-go/v2/schemaregistry"
	"github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/rules/encryption"
	"github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/rules/encryption/azurekms"
	"github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde"
	"github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde/avrov2"

	"my-platform-azure-go-client/internal/config"
	"my-platform-azure-go-client/internal/model"
)

func main() {
	if err := config.Validate(); err != nil {
		fmt.Fprintf(os.Stderr, "Configuration error: %v\n", err)
		os.Exit(1)
	}

	azurekms.Register()
	encryption.Register()

	topic, _ := config.GetTopic()
	srURL, _ := config.GetSchemaRegistryURL()

	producerCfg, err := config.GetProducerConfig()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to build producer config: %v\n", err)
		os.Exit(1)
	}

	p, err := kafka.NewProducer(producerCfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create producer: %v\n", err)
		os.Exit(1)
	}
	defer p.Close()

	srConfig := schemaregistry.NewConfig(srURL)

	client, err := schemaregistry.NewClient(srConfig)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create schema registry client: %v\n", err)
		os.Exit(1)
	}

	ruleConfig, err := config.GetAzureRuleConfig()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to read KMS credentials: %v\n", err)
		os.Exit(1)
	}

	serConfig := avrov2.NewSerializerConfig()
	serConfig.AutoRegisterSchemas = false
	serConfig.UseLatestVersion = true
	serConfig.RuleConfig = ruleConfig

	ser, err := avrov2.NewSerializer(client, serde.ValueSerde, serConfig)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create serializer: %v\n", err)
		os.Exit(1)
	}

	deliveryChan := make(chan kafka.Event, 1)
	defer close(deliveryChan)

	fmt.Printf("Producing user records to topic %s. ^C to exit.\n", topic)
	for i := 1; i <= 20; i++ {
		now := time.Now().UTC().Format(time.RFC3339Nano)
		record := model.PersonalData{
			ID:        fmt.Sprintf("%d", i),
			Name:      "Anna",
			Birthday:  time.Now().AddDate(-i, 0, 0).Format("2006-01-02"),
			Timestamp: &now,
		}

		payload, err := ser.Serialize(topic, &record)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Failed to serialize record %d: %v\n", i, err)
			continue
		}

		key := fmt.Sprintf("%d", i)
		err = p.Produce(&kafka.Message{
			TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
			Key:            []byte(key),
			Value:          payload,
		}, deliveryChan)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Produce failed for record %d: %v\n", i, err)
			continue
		}

		ev := <-deliveryChan
		m := ev.(*kafka.Message)
		if m.TopicPartition.Error != nil {
			fmt.Printf("Delivery failed for record %s: %v\n",
				string(m.Key), m.TopicPartition.Error)
		} else {
			fmt.Printf("PersonalData record %s successfully produced to %s [%d] at offset %v\n",
				string(m.Key), *m.TopicPartition.Topic,
				m.TopicPartition.Partition, m.TopicPartition.Offset)
		}
	}

	fmt.Println("\nFlushing records...")
	p.Flush(15 * 1000)
}
