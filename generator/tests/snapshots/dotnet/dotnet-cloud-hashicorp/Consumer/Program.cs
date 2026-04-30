using System;
using System.Threading;
using Avro.Generic;
using Confluent.Kafka;
using Confluent.Kafka.SyncOverAsync;
using Confluent.SchemaRegistry;
using Confluent.SchemaRegistry.Encryption;
using Confluent.SchemaRegistry.Encryption.HcVault;
using Confluent.SchemaRegistry.Serdes;
using CsfleDemo.Shared;

namespace CsfleDemo.Consumer;

internal static class Program
{
    private static int Main()
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

        HcVaultKmsDriver.Register();
        FieldEncryptionExecutor.Register();

        var topic = AppConfig.Topic;

        using var schemaRegistry = new CachedSchemaRegistryClient(new SchemaRegistryConfig
        {
            Url = AppConfig.SchemaRegistryUrl,
            BasicAuthCredentialsSource = AuthCredentialsSource.UserInfo,
            BasicAuthUserInfo = AppConfig.SchemaRegistryBasicAuthUserInfo,
        });

        var consumerConfig = new ConsumerConfig
        {
            BootstrapServers = AppConfig.BootstrapServers,
            GroupId = AppConfig.GroupId,
            AutoOffsetReset = Enum.Parse<AutoOffsetReset>(AppConfig.AutoOffsetReset, ignoreCase: true),
            SecurityProtocol = SecurityProtocol.SaslSsl,
            SaslMechanism = SaslMechanism.Plain,
            SaslUsername = AppConfig.KafkaSaslUsername,
            SaslPassword = AppConfig.KafkaSaslPassword,
        };

        var deserializerConfig = new AvroDeserializerConfig();
        foreach (var (k, v) in AppConfig.GetHcVaultRuleConfig())
        {
            deserializerConfig.Set(k, v);
        }

        using var consumer = new ConsumerBuilder<string, GenericRecord>(consumerConfig)
            .SetValueDeserializer(new AvroDeserializer<GenericRecord>(schemaRegistry, deserializerConfig).AsSyncOverAsync())
            .SetErrorHandler((_, e) => Console.Error.WriteLine($"Error: {e.Reason}"))
            .Build();

        consumer.Subscribe(topic);

        var cts = new CancellationTokenSource();
        Console.CancelKeyPress += (_, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };

        try
        {
            while (true)
            {
                var result = consumer.Consume(cts.Token);
                if (result?.Message?.Value == null)
                {
                    continue;
                }

                var record = result.Message.Value;
                record.TryGetValue("timestamp", out var ts);
                Console.WriteLine(
                    "--- Personal Data ---\n" +
                    $"  ID:        {GetField(record, "id")}\n" +
                    $"  Name:      {GetField(record, "name")}\n" +
                    $"  Birthday:  {GetField(record, "birthday")}\n" +
                    $"  Timestamp: {ts ?? "<nil>"}\n" +
                    "---------------------");
            }
        }
        catch (OperationCanceledException)
        {
            // Graceful shutdown on Ctrl+C.
        }
        finally
        {
            consumer.Close();
        }

        return 0;
    }

    private static object GetField(GenericRecord record, string field)
    {
        return record.TryGetValue(field, out var value) ? value : "<missing>";
    }
}
