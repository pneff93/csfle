using System;
using System.IO;
using System.Threading.Tasks;
using Avro;
using Avro.Generic;
using Confluent.Kafka;
using Confluent.SchemaRegistry;
using Confluent.SchemaRegistry.Encryption;
using Confluent.SchemaRegistry.Encryption.Azure;
using Confluent.SchemaRegistry.Serdes;
using CsfleDemo.Shared;

namespace CsfleDemo.Producer;

internal static class Program
{
    private static async Task<int> Main()
    {
        try
        {
            AppConfig.Validate();
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Configuration error: {ex.Message}");
            return 1;
        }

        AzureKmsDriver.Register();
        FieldEncryptionExecutor.Register();

        var topic = AppConfig.Topic;
        var schemaPath = AppConfig.ResolveSchemaPath();
        var schema = (RecordSchema)Avro.Schema.Parse(File.ReadAllText(schemaPath));

        using var schemaRegistry = new CachedSchemaRegistryClient(new SchemaRegistryConfig
        {
            Url = AppConfig.SchemaRegistryUrl
        });

        var serializerConfig = new AvroSerializerConfig
        {
            AutoRegisterSchemas = false,
            UseLatestVersion = true
        };
        foreach (var (k, v) in AppConfig.GetAzureRuleConfig())
        {
            serializerConfig.Set(k, v);
        }

        using var producer = new ProducerBuilder<string, GenericRecord>(new ProducerConfig
            {
                BootstrapServers = AppConfig.BootstrapServers
            })
            .SetValueSerializer(new AvroSerializer<GenericRecord>(schemaRegistry, serializerConfig))
            .Build();

        Console.WriteLine($"Producing user records to topic {topic}. ^C to exit.");

        for (int i = 1; i <= 20; i++)
        {
            var record = new GenericRecord(schema);
            record.Add("id", i.ToString());
            record.Add("name", "Anna");
            record.Add("birthday", DateTime.UtcNow.AddYears(-i).ToString("yyyy-MM-dd"));
            record.Add("timestamp", DateTime.UtcNow.ToString("o"));

            try
            {
                var dr = await producer.ProduceAsync(topic, new Message<string, GenericRecord>
                {
                    Key = i.ToString(),
                    Value = record
                });
                Console.WriteLine(
                    $"PersonalData record {dr.Key} successfully produced to {dr.Topic} [{dr.Partition.Value}] at offset {dr.Offset.Value}");
            }
            catch (ProduceException<string, GenericRecord> e)
            {
                Console.Error.WriteLine($"Delivery failed for record {i}: {e.Error.Reason}");
            }
        }

        Console.WriteLine("\nFlushing records...");
        producer.Flush(TimeSpan.FromSeconds(15));
        return 0;
    }
}
