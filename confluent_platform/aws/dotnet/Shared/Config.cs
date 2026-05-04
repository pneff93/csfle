using System;
using System.Collections.Generic;
using System.IO;

namespace CsfleDemo.Shared;

/// <summary>
/// Loads CSFLE demo configuration from the shared <c>../.env</c> file used by
/// the Python, Java, and Go clients. Variables already set in the environment
/// take precedence over values in <c>.env</c> (DotNetEnv is invoked via
/// <c>NoClobber()</c>), so the <c>export VAR=...</c> trick used in the
/// unauthorized-access test still works.
/// </summary>
public static class AppConfig
{
    static AppConfig()
    {
        foreach (var path in new[] { "../.env", "../../.env", ".env" })
        {
            if (File.Exists(path))
            {
                DotNetEnv.Env.NoClobber().Load(path);
                return;
            }
        }
    }

    public static string Topic => Get("KAFKA_TOPIC");
    public static string SchemaRegistryUrl => Get("SCHEMA_REGISTRY_URL");
    public static string BootstrapServers => Get("KAFKA_BOOTSTRAP_SERVERS");
    public static string GroupId => Get("KAFKA_GROUP_ID");
    public static string AutoOffsetReset => Get("KAFKA_AUTO_OFFSET_RESET");

    public static void Validate()
    {
        var required = new[]
        {
            "KAFKA_TOPIC",
            "KAFKA_BOOTSTRAP_SERVERS",
            "KAFKA_GROUP_ID",
            "KAFKA_AUTO_OFFSET_RESET",
            "SCHEMA_REGISTRY_URL",
            "AWS_KMS_KEY_NAME",
            "AWS_KMS_TYPE",
            "AWS_KMS_KEY_ID",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY"
        };
        foreach (var name in required) Get(name);
    }

    /// <summary>
    /// Returns AWS credentials packaged for the encryption rule config keys
    /// (<c>rules.access.key.id</c> / <c>rules.secret.access.key</c>) understood
    /// by <c>AvroSerializerConfig</c> and <c>AvroDeserializerConfig</c>.
    /// We pass them explicitly because the AWS SDK's env-var fallback inside
    /// the Confluent .NET driver doesn't always pick up vars loaded via
    /// <c>DotNetEnv</c> at runtime — passing them via rule config is the
    /// supported, deterministic path.
    /// </summary>
    public static Dictionary<string, string> GetAwsRuleConfig()
    {
        return new Dictionary<string, string>
        {
            ["rules.access.key.id"] = Get("AWS_ACCESS_KEY_ID"),
            ["rules.secret.access.key"] = Get("AWS_SECRET_ACCESS_KEY"),
        };
    }

    public static string ResolveSchemaPath()
    {
        var baseDir = AppContext.BaseDirectory;
        var candidates = new[]
        {
            Path.Combine(baseDir, "avro", "personal_data.avsc"),
            "avro/personal_data.avsc",
            "../avro/personal_data.avsc",
            "../../avro/personal_data.avsc"
        };
        foreach (var p in candidates)
        {
            if (File.Exists(p)) return p;
        }
        throw new FileNotFoundException(
            "Could not locate avro/personal_data.avsc relative to the current directory or executable.");
    }

    private static string Get(string name)
    {
        var value = Environment.GetEnvironmentVariable(name);
        if (string.IsNullOrEmpty(value))
        {
            throw new InvalidOperationException(
                $"Missing required configuration: {name}\n" +
                $"Please set it in ../.env (see ../.env.example).");
        }
        return value;
    }
}
