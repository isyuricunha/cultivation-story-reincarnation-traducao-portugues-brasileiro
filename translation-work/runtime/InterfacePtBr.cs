using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using HarmonyLib;
using Newtonsoft.Json.Linq;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

internal static class InterfacePtBr
{
    private sealed class Rule
    {
        public string Path;
        public string Component;
        public string Source;
        public string Target;
        public string Mode;
        public Regex Pattern;
    }

    private static readonly Dictionary<string, List<Rule>> Rules =
        new Dictionary<string, List<Rule>>(StringComparer.Ordinal);

    internal static void Install(Harmony harmony, JArray translations, JArray layout)
    {
        foreach (JObject row in translations)
            Add(row);
        if (layout != null)
            foreach (JObject row in layout)
                Add(row);

        var flags = new HarmonyMethod(typeof(InterfacePtBr), "OnEnable");
        harmony.Patch(AccessTools.DeclaredMethod(typeof(Graphic), "OnEnable"), postfix: flags);
        harmony.Patch(AccessTools.PropertySetter(typeof(TMP_Text), "text"),
            prefix: new HarmonyMethod(typeof(InterfacePtBr), "SetText"));
        harmony.Patch(AccessTools.PropertySetter(typeof(Text), "text"),
            prefix: new HarmonyMethod(typeof(InterfacePtBr), "SetText"));
    }

    private static void Add(JObject row)
    {
        var rule = new Rule
        {
            Path = (string)row["path"],
            Component = (string)row["component"],
            Source = (string)row["ZH_CN"],
            Target = (string)row["PTBR"],
            Mode = (string)row["mode"]
        };
        if (rule.Mode == "format")
            rule.Pattern = new Regex("^" + Regex.Escape(rule.Source).Replace(@"\{0}", "([0-9]+(?:/[0-9]+)?|MAX)") + "$",
                RegexOptions.CultureInvariant);
        string name = rule.Path.Substring(rule.Path.LastIndexOf('/') + 1);
        List<Rule> entries;
        if (!Rules.TryGetValue(name, out entries))
        {
            entries = new List<Rule>();
            Rules.Add(name, entries);
        }
        entries.Add(rule);
    }

    private static string Hierarchy(Transform transform)
    {
        var names = new Stack<string>();
        for (; transform != null; transform = transform.parent)
            names.Push(transform.name.EndsWith("(Clone)", StringComparison.Ordinal)
                ? transform.name.Substring(0, transform.name.Length - 7) : transform.name);
        return String.Join("/", names.ToArray());
    }

    private static bool Lookup(Graphic label, string original, out string translated)
    {
        translated = original;
        List<Rule> entries;
        if (original == null || !Rules.TryGetValue(label.name, out entries))
            return false;
        string path = Hierarchy(label.transform);
        string component = label is TMP_Text ? "tmp" : "legacy";
        foreach (var rule in entries)
        {
            if (rule.Component != component ||
                !(path == rule.Path || path.EndsWith("/" + rule.Path, StringComparison.Ordinal)))
                continue;
            if (rule.Mode == "fit")
                return true;
            if (rule.Pattern != null)
            {
                var match = rule.Pattern.Match(original.Replace('：', ':'));
                if (!match.Success)
                    continue;
                translated = rule.Target.Replace("{0}", match.Groups[1].Value);
                return true;
            }
            if (!String.Equals(rule.Source.Trim(), original.Trim(), StringComparison.Ordinal))
                continue;
            translated = rule.Mode == "hide" ? "" : rule.Target;
            return true;
        }
        return false;
    }

    private static void SetText(Graphic __instance, ref string __0)
    {
        string translated;
        if (Lookup(__instance, __0, out translated))
        {
            Fit(__instance);
            __0 = translated;
        }
    }

    private static void OnEnable(Graphic __instance)
    {
        var tmp = __instance as TMP_Text;
        var legacy = __instance as Text;
        if (tmp == null && legacy == null)
            return;

        string original = tmp != null ? tmp.text : legacy.text;
        string translated;
        if (!Lookup(__instance, original, out translated))
            return;

        Fit(__instance);
        if (tmp != null)
            tmp.text = translated;
        else
            legacy.text = translated;
    }

    private static void Fit(Graphic label)
    {
        var tmp = label as TMP_Text;
        if (tmp != null)
        {
            if (!tmp.enableAutoSizing)
            {
                tmp.fontSizeMax = tmp.fontSize;
                tmp.fontSizeMin = Math.Max(1f, tmp.fontSize * 0.5f);
                tmp.enableAutoSizing = true;
            }
            tmp.enableWordWrapping = false;
        }
        else
        {
            var legacy = (Text)label;
            if (!legacy.resizeTextForBestFit)
            {
                legacy.resizeTextMaxSize = legacy.fontSize;
                legacy.resizeTextMinSize = Math.Max(1, legacy.fontSize / 2);
                legacy.resizeTextForBestFit = true;
            }
        }
    }
}
