"""Verified Unity TextAsset table extraction and portable translation delta."""
import hashlib
import json
from struct import unpack_from

DEPLOY = 'Re-xiuxian Legend_Data/StreamingAssets/json'
PLUGIN = 'BepInEx/plugins/CultivationPtBr/CultivationPtBr.dll'
DELTA = 'BepInEx/plugins/CultivationPtBr/tables.ptbr.json'


class FormatError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise FormatError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate JSON property: {key}')
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw, strict=False, object_pairs_hook=unique)


def read_source(path, shape):
    try:
        import UnityPy
    except ImportError as error:
        raise FormatError('UnityPy required only for local source import; install requirements-import.txt') from error
    raw = path.read_bytes()
    require(raw.startswith(b'UnityFS\0'), 'Expected an original UnityFS bundle')
    assets = {}
    names = set()
    for obj in UnityPy.load(raw).objects:
        if obj.type.name == 'AssetBundle':
            continue
        require(obj.type.name == 'TextAsset', 'Unexpected object in table bundle')
        asset = obj.read()
        name = asset.m_Name
        require(name not in names, f'Duplicate TextAsset: {name}')
        names.add(name)
        if name in shape['tables']:
            serialized = obj.get_raw_data()
            endian = obj.reader.endian
            name_len, = unpack_from(endian + 'I', serialized)
            start = (4 + name_len + 3) & ~3
            require(serialized[4:4 + name_len].decode('utf-8') == name and start + 4 <= len(serialized),
                    f'Invalid serialized TextAsset name: {name}')
            length, = unpack_from(endian + 'I', serialized, start)
            end = start + 4 + length
            require(end <= len(serialized) and len(serialized) - end < 4,
                    f'Unexpected serialized TextAsset layout: {name}')
            payload = serialized[start + 4:end]
            require(payload.decode('utf-8-sig') == asset.m_Script.lstrip('\ufeff'),
                    f'Lossless TextAsset extraction failed: {name}')
            assets[name] = payload
    require(names == set(shape['tables']) | set(shape['excluded']),
            f'Unity table inventory changed: {sorted(names ^ (set(shape["tables"]) | set(shape["excluded"])))}')
    return raw, assets


def table_rows(raw, name):
    obj = parse(raw)
    array = name + 's'
    require(isinstance(obj, dict) and list(obj) == [array] and isinstance(obj[array], list),
            f'Unexpected root for {name}')
    rows = obj[array]
    ids = [r.get('Id') for r in rows]
    require(all(type(i) is int and -(2**31) <= i < 2**31 for i in ids)
            and len(ids) == len(set(ids)), f'Invalid or duplicate native ID: {name}')
    return rows


def catalog(assets, shape):
    data = {name: table_rows(assets[name], name) for name in shape['tables']}
    events = {}
    for event in data.get('EventInfo', []):
        for field in ('PreDialog', 'WinDialog', 'LoseDialog'):
            for dialogue_id in event.get(field, []):
                events.setdefault(dialogue_id, []).append({
                    'event_id': event['Id'], 'link': field, 'label': event.get('Name'),
                    'event_character': event.get('Character'), 'location': event.get('Location'),
                })
    records = []
    for name, fields in shape['tables'].items():
        for row, record in enumerate(data[name]):
            for field in fields:
                require(field in record and isinstance(record[field], str),
                        f'Unexpected field: {name}/{record["Id"]}/{field}')
                value = record[field]
                if not value.strip():
                    continue
                context = {'text_type': name, 'field': field}
                if name == 'DialogueInfo':
                    context['event_links'] = events.get(record['Id'], [])
                records.append({
                    'id': f'{name}/{record["Id"]}/{field}', 'key': record['Id'],
                    'row': row, 'source_file': DEPLOY, 'table': name, 'context': context,
                    'ZH_CN': value, 'PTBR': '',
                })
    require(records, 'No localization records')
    return records


def make_delta(records, hashes):
    tables = {name: {'sha256': digest, 'rows': {}} for name, digest in hashes.items()}
    for r in records:
        group = tables[r['table']]['rows'].setdefault(str(r['key']), {})
        field = r['context']['field']
        require(field not in group, 'Duplicate patch address')
        group[field] = r['PTBR']
    return {'schema': 1, 'tables': tables}


def apply_table(raw, name, delta):
    require(sha(raw) == delta['sha256'], f'Native checksum mismatch: {name}')
    rows = table_rows(raw, name)
    by_id = {str(row['Id']): row for row in rows}
    for key, fields in delta['rows'].items():
        require(key in by_id, f'Unknown native ID: {name}/{key}')
        row = by_id[key]
        for field, text in fields.items():
            require(isinstance(row.get(field), str) and isinstance(text, str),
                    f'Invalid native field: {name}/{key}/{field}')
            row[field] = text
    return {name + 's': rows}
