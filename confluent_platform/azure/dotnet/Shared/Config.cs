using System;
using System.Collections.Generic;
using System.IO;

namespace CsfleDemo.Shared;

/// <summary>
/// Loads CSFLE demo configuration from the shared <c>../.env</c> file used by
/// the Python client. Variables already set in the environment take precedence
/// over values in <c>.env</c> (DotNetEnv is invoked via <c>NoClobber()</c>),
/// so the <c>export VAR=...</c> trick used in the unauthorized-access test
/// still works.
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
            "AZURE_KMS_KEY_NAME",
            "AZURE_KMS_TYPE",
            "AZURE_KMS_KEY_ID",
            "AZURE_TENANT_ID",
            "AZURE_CLIENT_ID",
            "AZURE_CLIENT_SECRET"
        };
        foreach (var name in required) Get(name);
    }

    /// <summary>
    /// Returns Azure service-principal credentials packaged for the encryption
    /// rule config keys (<c>rules.tenant.id</c> / <c>rules.client.id</c> /
    /// <c>rules.client.secret</c>) understood by <c>AvroSerializerConfig</c>
    /// and <c>AvroDeserializerConfig</c>. Passing them explicitly avoids any
    /// ambiguity in Azure SDK default credential resolution.
    /// </summary>
    public static Dictionary<string, string> GetAzureRuleConfig()
    {
        return new Dictionary<string, string>
        {
            ["rules.tenant.id"] = Get("AZURE_TENANT_ID"),
            ["rules.client.id"] = Get("AZURE_CLIENT_ID"),
            ["rules.client.secret"] = Get("AZURE_CLIENT_SECRET"),
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
