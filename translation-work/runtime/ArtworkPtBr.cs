using System;
using System.Collections.Generic;
using System.IO;
using BepInEx.Logging;
using HarmonyLib;
using Newtonsoft.Json.Linq;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Sprites;

internal static class ArtworkPtBr
{
    private sealed class Replacement
    {
        public string File;
        public int Width;
        public int Height;
        public Rect Crop;
        public Sprite Sprite;
        public bool Failed;
    }

    private static readonly Dictionary<string, Replacement> Replacements =
        new Dictionary<string, Replacement>(StringComparer.Ordinal);
    private static ManualLogSource log;

    internal static void Install(Harmony harmony, ManualLogSource logger, string folder, JArray artwork)
    {
        log = logger;
        foreach (JObject row in artwork)
        {
            string filename = (string)row["file"];
            if (Path.GetFileName(filename) != filename)
                throw new InvalidDataException("Invalid sprite file name: " + filename);
            var crop = (JArray)row["crop"];
            Replacements.Add((string)row["sprite"], new Replacement
            {
                File = Path.Combine(folder, "art", filename),
                Width = (int)row["width"],
                Height = (int)row["height"],
                Crop = new Rect((int)crop[0], (int)crop[1], (int)crop[2], (int)crop[3])
            });
        }

        harmony.Patch(AccessTools.PropertySetter(typeof(Image), "sprite"),
            prefix: new HarmonyMethod(typeof(ArtworkPtBr), "SetSprite"));
        harmony.Patch(AccessTools.PropertySetter(typeof(Image), "overrideSprite"),
            prefix: new HarmonyMethod(typeof(ArtworkPtBr), "SetSprite"));
        harmony.Patch(AccessTools.DeclaredMethod(typeof(Image), "OnEnable"),
            postfix: new HarmonyMethod(typeof(ArtworkPtBr), "OnEnable"));
    }

    private static void SetSprite(ref Sprite __0)
    {
        if (__0 == null)
            return;
        string name = __0.name;
        if (name.EndsWith("(Clone)", StringComparison.Ordinal))
            name = name.Substring(0, name.Length - 7);
        Replacement replacement;
        if (!Replacements.TryGetValue(name, out replacement) || replacement.Failed)
            return;
        if (__0.rect.width != replacement.Width || __0.rect.height != replacement.Height)
            return;

        if (replacement.Sprite == null)
        {
            Texture2D source = null;
            Texture2D texture = null;
            try
            {
                source = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                if (!ImageConversion.LoadImage(source, File.ReadAllBytes(replacement.File), false))
                    throw new InvalidDataException("Invalid sprite PNG: " + replacement.File);
                var original = __0;
                texture = RenderSprite(source, replacement.Crop, original);
                var pivot = new Vector2(original.pivot.x / original.rect.width, original.pivot.y / original.rect.height);
                replacement.Sprite = Sprite.Create(texture, new Rect(0, 0, texture.width, texture.height), pivot,
                    original.pixelsPerUnit, 0, SpriteMeshType.FullRect, original.border);
                replacement.Sprite.name = original.name + " [PT-BR]";
            }
            catch (Exception error)
            {
                replacement.Failed = true;
                if (texture != null)
                    UnityEngine.Object.Destroy(texture);
                log.LogWarning(error.Message);
                return;
            }
            finally
            {
                if (source != null)
                    UnityEngine.Object.Destroy(source);
            }
        }
        __0 = replacement.Sprite;
    }

    private static Texture2D RenderSprite(Texture2D source, Rect crop, Sprite original)
    {
        int width = (int)original.rect.width;
        int height = (int)original.rect.height;
        var pad = DataUtility.GetPadding(original);
        float availableWidth = width - pad.x - pad.z;
        float availableHeight = height - pad.y - pad.w;
        if (availableWidth <= 0f || availableHeight <= 0f)
            throw new InvalidDataException("Empty sprite geometry: " + original.name);
        float scale = Math.Min(availableWidth / crop.width, availableHeight / crop.height);
        int drawWidth = Math.Max(1, Mathf.RoundToInt(crop.width * scale));
        int drawHeight = Math.Max(1, Mathf.RoundToInt(crop.height * scale));
        int left = Mathf.Clamp(Mathf.RoundToInt(pad.x + (availableWidth - drawWidth) / 2f), 0, width - drawWidth);
        int bottom = Mathf.Clamp(Mathf.RoundToInt(pad.y + (availableHeight - drawHeight) / 2f), 0, height - drawHeight);
        var pixels = new Color32[width * height];
        for (int y = 0; y < drawHeight; y++)
        {
            float v = (crop.y + (y + 0.5f) * crop.height / drawHeight) / source.height;
            for (int x = 0; x < drawWidth; x++)
            {
                float u = (crop.x + (x + 0.5f) * crop.width / drawWidth) / source.width;
                pixels[(bottom + y) * width + left + x] = source.GetPixelBilinear(u, v);
            }
        }
        var texture = new Texture2D(width, height, TextureFormat.RGBA32, false);
        texture.wrapMode = TextureWrapMode.Clamp;
        texture.SetPixels32(pixels);
        texture.Apply(false, true);
        return texture;
    }

    private static void OnEnable(Image __instance)
    {
        var original = __instance.sprite;
        var translated = original;
        SetSprite(ref translated);
        if (translated != original)
            __instance.sprite = translated;
    }
}
