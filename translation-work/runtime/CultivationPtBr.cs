using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEngine;

[BepInPlugin("br.yuricunha.cultivation.ptbr", "Cultivation PT-BR", "1.0.0")]
public sealed class CultivationPtBr : BaseUnityPlugin
{
    private static ManualLogSource log;
    private static JObject tables;
    private static readonly HashSet<string> Reported = new HashSet<string>();

    private void Awake()
    {
        log = Logger;
        try
        {
            var path = Path.Combine(Path.GetDirectoryName(typeof(CultivationPtBr).Assembly.Location), "tables.ptbr.json");
            var spec = Parse(File.ReadAllText(path, Encoding.UTF8));
            if ((int)spec["schema"] != 1)
                throw new InvalidDataException("Unsupported translation schema");
            tables = (JObject)spec["tables"];
            var harmony = new Harmony("br.yuricunha.cultivation.ptbr");
            harmony.Patch(AccessTools.PropertyGetter(typeof(TextAsset), "text"),
                postfix: new HarmonyMethod(typeof(CultivationPtBr), "Localize"));
        }
        catch (Exception error)
        {
            log.LogError(error);
        }
    }

    private static JObject Parse(string text)
    {
        using (var reader = new JsonTextReader(new StringReader(text)))
        {
            reader.DateParseHandling = DateParseHandling.None;
            return JObject.Load(reader, new JsonLoadSettings
            {
                DuplicatePropertyNameHandling = DuplicatePropertyNameHandling.Error
            });
        }
    }

    public static string Apply(string name, byte[] raw, string original, JObject spec)
    {
        string digest;
        using (var hash = SHA256.Create())
            digest = BitConverter.ToString(hash.ComputeHash(raw)).Replace("-", "").ToLowerInvariant();
        if (!String.Equals(digest, (string)spec["sha256"], StringComparison.Ordinal))
            throw new InvalidDataException("Source checksum mismatch for " + name);

        var data = Parse(original);
        var index = new Dictionary<string, JObject>(StringComparer.Ordinal);
        foreach (JObject row in (JArray)data[name + "s"])
        {
            if (row["Id"].Type != JTokenType.Integer)
                throw new InvalidDataException("Invalid native ID in " + name);
            index.Add(((int)row["Id"]).ToString(CultureInfo.InvariantCulture), row);
        }

        foreach (var entry in ((JObject)spec["rows"]).Properties())
        {
            var row = index[entry.Name];
            foreach (var field in ((JObject)entry.Value).Properties())
            {
                if (row[field.Name] == null || row[field.Name].Type != JTokenType.String ||
                    field.Value.Type != JTokenType.String)
                    throw new InvalidDataException("Invalid translation field " + field.Name);
                row[field.Name] = field.Value.DeepClone();
            }
        }
        return data.ToString(Formatting.None);
    }

    private static void Localize(TextAsset __instance, ref string __result)
    {
        var name = __instance.name;
        var spec = tables[name] as JObject;
        if (spec == null)
            return;

        try
        {
            __result = Apply(name, __instance.bytes, __result, spec);
            if (Reported.Add(name))
                log.LogInfo("Localized " + name);
        }
        catch (Exception error)
        {
            if (Reported.Add(name))
                log.LogWarning(error.Message);
        }
    }
}
