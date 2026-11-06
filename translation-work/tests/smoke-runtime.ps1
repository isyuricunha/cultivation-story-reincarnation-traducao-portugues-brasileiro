param([Parameter(Mandatory)][string]$GameRoot)
$ErrorActionPreference = 'Stop'
$work = Split-Path -Parent $PSScriptRoot
$root = Split-Path -Parent $work
$managed = Join-Path $GameRoot 'Re-xiuxian Legend_Data/Managed'
$core = Join-Path $GameRoot 'BepInEx/core'
foreach ($library in @(
    "$managed/UnityEngine.CoreModule.dll",
    "$managed/UnityEngine.dll",
    "$core/BepInEx.dll",
    "$core/0Harmony.dll",
    "$managed/Newtonsoft.Json.dll"
)) {
    [void][Reflection.Assembly]::LoadFrom($library)
}
$assembly = [Reflection.Assembly]::LoadFrom("$work/runtime/CultivationPtBr.dll")
$method = $assembly.GetType('CultivationPtBr').GetMethod('Apply')

function Get-SourceHash([byte[]]$Bytes) {
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}

$fixture = '{"DialogueInfos":[{"Id":7,"Chinese":"a{0}","Other":42}]}'
$bytes = [Text.Encoding]::UTF8.GetBytes($fixture)
$hash = Get-SourceHash $bytes
$spec = [Newtonsoft.Json.Linq.JObject]::Parse('{"sha256":"' + $hash + '","rows":{"7":{"Chinese":"\u00e1 {0}"}}}')
$result = $method.Invoke($null, [object[]]@('DialogueInfo', $bytes, $fixture, $spec))
$expected = '{"DialogueInfos":[{"Id":7,"Chinese":"\u00e1 {0}","Other":42}]}'
if (![Newtonsoft.Json.Linq.JToken]::DeepEquals(
    [Newtonsoft.Json.Linq.JObject]::Parse($expected),
    [Newtonsoft.Json.Linq.JObject]::Parse($result)
)) {
    throw 'Runtime fixture changed unexpected fields or lost UTF-8 text'
}

$count = 0
foreach ($file in [IO.Directory]::EnumerateFiles("$root/EN/TextAsset", '*.json')) {
    $name = [IO.Path]::GetFileNameWithoutExtension($file)
    $bytes = [IO.File]::ReadAllBytes($file)
    $raw = [Text.Encoding]::UTF8.GetString($bytes).TrimStart([char]0xFEFF)
    $hash = Get-SourceHash $bytes
    $spec = [Newtonsoft.Json.Linq.JObject]::Parse('{"sha256":"' + $hash + '","rows":{}}')
    $result = $method.Invoke($null, [object[]]@($name, $bytes, $raw, $spec))
    if (![Newtonsoft.Json.Linq.JToken]::DeepEquals(
        [Newtonsoft.Json.Linq.JObject]::Parse($raw),
        [Newtonsoft.Json.Linq.JObject]::Parse($result)
    )) {
        throw "Semantic round-trip failed for $name"
    }
    $count++
}
if (!$count) { throw 'No native fixtures imported into EN/TextAsset' }
"Runtime parser preserved $count original tables and applied the synthetic UTF-8 delta."
