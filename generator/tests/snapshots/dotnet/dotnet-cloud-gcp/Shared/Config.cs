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
            "GCP_KMS_KEY_NAME",
            "GCP_KMS_TYPE",
            "GCP_KMS_KEY_ID",
            "GCP_CLIENT_ID",
            "GCP_CLIENT_EMAIL",
            "GCP_PRIVATE_KEY_ID",
            "GCP_PRIVATE_KEY",
        };
        foreach (var name in required) Get(name);
    }

    public static Dictionary<string, string> GetGcpRuleConfig()
    {
        return new Dictionary<string, string>
        {
            ["rules.client.id"] = Get("GCP_CLIENT_ID"),
            ["rules.client.email"] = Get("GCP_CLIENT_EMAIL"),
            ["rules.private.key.id"] = Get("GCP_PRIVATE_KEY_ID"),
            // dotnet's DotNetEnv preserves the literal `\n` escapes inside the
            // double-quoted PEM, so we unescape them here before handing to the driver.
            ["rules.private.key"] = Get("GCP_PRIVATE_KEY").Replace("\\n", "\n"),
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
