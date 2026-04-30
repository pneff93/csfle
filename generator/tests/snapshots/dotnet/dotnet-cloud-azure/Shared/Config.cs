using System;
using System.Collections.Generic;
using System.IO;

namespace CsfleDemo.Shared;

/// <summary>
/// Loads CSFLE demo configuration from this project's <c>.env</c> file.
/// Variables already set in the environment take precedence over values
/// in <c>.env</c> (DotNetEnv is invoked via <c>NoClobber()</c>), so the
/// <c>export VAR=...</c> trick used in the unauthorized-access test still works.
/// </summary>
public static class AppConfig
{
    static AppConfig()
    {
        // Producer/Consumer binaries run from bin/Debug/net8.0/, so .env
        // is several levels up. Try a few candidate paths to find it.
        foreach (var path in new[] { ".env", "../.env", "../../.env", "../../../.env", "../../../../.env" })
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
    public static string KafkaSaslUsername => Get("KAFKA_SASL_USERNAME");
    public static string KafkaSaslPassword => Get("KAFKA_SASL_PASSWORD");
    public static string SchemaRegistryBasicAuthUserInfo => Get("SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO");

    public static void Validate()
    {
        var required = new[]
        {
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
        };
        foreach (var name in required) Get(name);
    }

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
                $"Please set it in .env (see .env.example).");
        }
        return value;
    }
}
