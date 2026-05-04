package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/confluentinc/confluent-kafka-go/v2/schemaregistry"
	"github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/rules/encryption"
	"github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/rules/encryption/azurekms"
	"github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde"
	"github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde/avrov2"

	"csfle-azure-go-demo/internal/config"
	"csfle-azure-go-demo/internal/model"
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

	consumerCfg, err := config.GetConsumerConfig()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to build consumer config: %v\n", err)
		os.Exit(1)
	}

	c, err := kafka.NewConsumer(consumerCfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create consumer: %v\n", err)
		os.Exit(1)
	}
	defer c.Close()

	client, err := schemaregistry.NewClient(schemaregistry.NewConfig(srURL))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create schema registry client: %v\n", err)
		os.Exit(1)
	}

	ruleConfig, err := config.GetAzureRuleConfig()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to read Azure credentials: %v\n", err)
		os.Exit(1)
	}

	deserConfig := avrov2.NewDeserializerConfig()
	deserConfig.RuleConfig = ruleConfig

	deser, err := avrov2.NewDeserializer(client, serde.ValueSerde, deserConfig)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create deserializer: %v\n", err)
		os.Exit(1)
	}

	if err := c.SubscribeTopics([]string{topic}, nil); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to subscribe to topic %s: %v\n", topic, err)
		os.Exit(1)
	}

	sigchan := make(chan os.Signal, 1)
	signal.Notify(sigchan, syscall.SIGINT, syscall.SIGTERM)

	run := true
	for run {
		select {
		case sig := <-sigchan:
			fmt.Printf("Caught signal %v: terminating\n", sig)
			run = false
		default:
			ev := c.Poll(1000)
			if ev == nil {
				continue
			}
			switch e := ev.(type) {
			case *kafka.Message:
				var pd model.PersonalData
				if err := deser.DeserializeInto(*e.TopicPartition.Topic, e.Value, &pd); err != nil {
					fmt.Fprintf(os.Stderr, "Failed to deserialize payload: %v\n", err)
				} else {
					fmt.Println(pd.String())
				}
			case kafka.Error:
				fmt.Fprintf(os.Stderr, "Error: %v: %v\n", e.Code(), e)
			}
		}
	}
}
