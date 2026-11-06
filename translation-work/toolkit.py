"""Manual localization CLI. Python standard library only; never writes to a game."""
import argparse
import collections
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
sys.dont_write_bytecode = True

from native import DEPLOY, PLUGIN, DELTA, catalog, read_source, require, sha, make_delta, apply_table, parse
from storage import Store, canonical, digest, encoded, safe
ROOT = Path(__file__).resolve().parent.parent
WORK = 'translation-work/'
TRANS = WORK + 'translations/'
MANIFEST = TRANS + 'manifest.json'
CATALOG = TRANS + 'source-catalog.json'


def load(path):
    return json.loads(path.read_text('utf-8-sig'))


def lines(records):
    return b''.join((json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n').encode()
                    for x in records)


def immutable(record):
    return {k: v for k, v in record.items() if k != 'PTBR'}


def protected(text):
    matches = re.finditer(r'\[[a-zA-Z][^\]\n]*\]|\{(?:[0-9]+|[a-zA-Z_]\w*)(?::[^}]+)?\}'
                         r'|%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[sdfiu]|<[^>\n]+>', text)
    tokens = []
    for match in matches:
        token = match.group()
        # Numeric percentages followed by words (3% discount, 98% de certeza)
        # are prose, not printf's space flag. Retain actual %d, %02d, % d, etc.
        if (re.fullmatch(r'% +[sdfiu]', token) and match.start() > 0
                and text[match.start() - 1].isdigit() and match.end() < len(text)
                and text[match.end()].isalpha()):
            continue
        tokens.append(token)
    return collections.Counter(tokens)


def validate_text(source, target):
    require(isinstance(target, str), 'PTBR must be a string')
    require(not any(ord(c) < 32 and c not in '\n\r\t' for c in target), 'Invalid control character')
    require(len(target.encode('utf-8')) <= 4 * 1024 * 1024, 'Text exceeds native safety limit')
    require(protected(source) == protected(target), 'Protected tokens/tags differ')
    stack = []
    for close, tag, attrs in re.findall(r'<(/?)([A-Za-z]+)([^>]*)>', target):
        if tag.lower() in ('br', 'sprite', 'space', 'page') or attrs.endswith('/'):
            continue
        if close:
            require(stack and stack.pop() == tag, 'Unbalanced/nested rich text')
        else:
            stack.append(tag)
    require(not stack, 'Unclosed rich text tag')


class Project:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.shape = load(self.root / WORK / 'engine-shapes.json')
        self.config = load(self.root / WORK / 'project.json')
        require(self.config['schema'] == 1, 'Unsupported project schema')
        self.store = Store(self.root, self.config['retention']['count'],
                           self.config['retention']['bytes'])

    def integrity(self):
        runtime = load(self.root / WORK / 'runtime-support.json')
        require(runtime['schema'] == 1, 'Invalid runtime receipt')
        tool = safe(self.root, runtime['toolchain']['path'])
        require(sha(canonical(tool.read_bytes())) == runtime['toolchain']['sha256'],
                'Toolchain receipt checksum mismatch')
        receipt = load(tool)
        for rel, expected in receipt['files'].items():
            raw = safe(self.root, rel).read_bytes()
            require(sha(raw if rel.endswith('.dll') else canonical(raw)) == expected,
                    'Toolchain checksum mismatch: ' + rel)
        return runtime

    def workspace(self, source=True):
        self.store.assert_ready()
        manifest = load(self.root / MANIFEST)
        accepted = load(self.root / CATALOG)
        require(sha(encoded(accepted)) == manifest['catalog_sha256'], 'Accepted catalog tampered')
        if source:
            require(manifest['shape_sha256'] == sha(canonical((self.root / WORK /
                    'engine-shapes.json').read_bytes())), 'Engine profile differs from accepted source')
        require(manifest['generation'] == sha(encoded({'source': manifest['source_sha256'],
                'catalog': manifest['catalog_sha256']})), 'Invalid source generation')
        known = {r['id']: r for r in accepted}
        require(len(known) == len(accepted) == manifest['record_count'], 'Bad catalog inventory')
        found, batches, owners = {}, {}, {}
        expected_names = set(manifest['batches'])
        actual_names = {p.name for p in (self.root / TRANS).glob('batch-*.jsonl')}
        require(actual_names == expected_names, 'Unexpected/missing batch files')
        for name in manifest['batches']:
            path = safe(self.root, TRANS + name)
            records = [json.loads(line) for line in path.read_text('utf-8').splitlines()]
            require(0 < len(records) <= manifest['batch_size'], 'Invalid batch size: ' + name)
            batches[name] = records
            for r in records:
                key = r['id']
                require(key in known and key not in found, 'Unknown/duplicate ID: ' + key)
                require(immutable(r) == known[key], 'Immutable source/context changed: ' + key)
                validate_text(r['ZH_CN'], r['PTBR']) if r['PTBR'] else require(
                    isinstance(r['PTBR'], str), 'PTBR must be a string')
                found[key], owners[key] = r, name
        require(set(found) == set(known), 'Missing translation records')
        if source and (self.root / 'EN').exists():
            for rel, expected in manifest['source_hashes'].items():
                require(digest(safe(self.root, 'EN/' + rel)) == expected,
                        'Local EN differs from accepted source: use sync')
        self.store.assert_ready()
        return manifest, found, batches, owners

    def source_data(self, folder):
        paths = [DEPLOY, *('TextAsset/' + name + '.json' for name in self.shape['tables'])]
        return {rel: safe(folder, rel).read_bytes() for rel in paths}

    def fingerprint(self, records):
        return sha(lines(sorted(records.values(), key=lambda row: row['id'])))

    def expectations(self, extra=()):
        names = [MANIFEST, CATALOG, *extra, 'EN/' + DEPLOY, *('EN/TextAsset/' + name + '.json' for name in self.shape['tables'])]
        names += [str(p.relative_to(self.root)).replace('\\', '/')
                  for p in (self.root / TRANS).glob('batch-*.jsonl')]
        return {name: digest(safe(self.root, name)) for name in names}

    def current_guard(self, expected):
        require(all(digest(safe(self.root, p)) == d for p, d in expected.items()),
                'Concurrent edit while planning: retry against current work')

    def candidate(self, game=None, file=None, tree=None):
        if game:
            base = Path(game).resolve()
            info = safe(base, 'Re-xiuxian Legend_Data/app.info')
            require(info.is_file() and info.read_text('utf-8-sig').splitlines() ==
                    ['Collider Studio', 'Re-xiuxian Legend'], 'Wrong game: app.info identity mismatch')
            require(not base.is_relative_to(self.root), 'Game input must be external')
            file = safe(base, DEPLOY)
        if file:
            raw, assets = read_source(Path(file).resolve(), self.shape)
            data = {DEPLOY: raw, **{'TextAsset/' + name + '.json': value for name, value in assets.items()}}
        else:
            data = self.source_data(Path(tree).resolve() if tree else self.root / 'EN')
            assets = {name: data['TextAsset/' + name + '.json'] for name in self.shape['tables']}
            raw, native = read_source((Path(tree).resolve() if tree else self.root / 'EN') / DEPLOY, self.shape)
            require(raw == data[DEPLOY] and native == assets, 'Local TextAssets differ from bundle; reimport it')
        rows = catalog(assets, self.shape)
        for name, payload in assets.items():
            require(apply_table(payload, name, {'sha256': sha(payload), 'rows': {}}) == parse(payload),
                    'Table no-op changes structure: ' + name)
        return data, rows

    def discover(self):
        candidates = list(self.config.get('game_candidates', []))
        roots = [Path('C:/Program Files (x86)/Steam'), Path.home() / '.steam/steam',
                 Path.home() / '.local/share/Steam']
        for steam in roots:
            libraries = [steam]
            vdf = steam / 'steamapps/libraryfolders.vdf'
            if vdf.is_file():
                libraries += [Path(x.replace('\\\\', '\\')) for x in
                              re.findall(r'"path"\s+"([^"]+)"', vdf.read_text('utf-8'))]
            for lib in libraries:
                manifest = lib / 'steamapps/appmanifest_3458620.acf'
                if manifest.is_file():
                    matches = re.findall(r'"installdir"\s+"([^"]+)"', manifest.read_text('utf-8'))
                    if len(matches) == 1:
                        candidates.append(str(lib / 'steamapps/common' / matches[0]))
        verified = []
        for value in sorted(set(candidates)):
            if (Path(value) / DEPLOY).exists():
                self.candidate(game=value)
                verified.append(value)
        require(len(verified) == 1, 'No unique verified local install. Use: '
                'python translation-work/toolkit.py update-sources --game-root "PATH_TO_GAME"')
        return verified[0]

    def synchronize(self, data, incoming, initial=False, dry=False, batch_size=None):
        manifest_path = self.root / MANIFEST
        require(not initial or not manifest_path.exists(), 'extract refuses existing progress; use sync')
        expected = self.expectations(['EN/' + DEPLOY])
        if initial:
            old_m, old, batches, owners = {}, {}, {}, {}
        else:
            old_m, old, batches, owners = self.workspace(source=False)
        accepted = [immutable(r) for r in incoming]
        generation = sha(encoded({'source': sha(encoded({rel: sha(raw) for rel, raw in data.items()})), 'catalog': sha(encoded(accepted))}))
        shape_hash = sha(canonical((self.root / WORK / 'engine-shapes.json').read_bytes()))
        if generation == old_m.get('generation') and shape_hash == old_m.get('shape_sha256'):
            imports = {'EN/' + rel: raw for rel, raw in data.items()
                       if expected.get('EN/' + rel) != sha(raw)}
            if not imports:
                return {'status': 'unchanged', 'generation': generation}
            if not dry:
                self.current_guard(expected)
            transaction = None if dry else self.store.commit(imports, expected)
            return {'status': 'dry-run' if dry else 'sources-restored',
                    'generation': generation, 'files': sorted(imports), 'transaction': transaction}
        old_hashes = old_m.get('source_hashes', {DEPLOY: old_m.get('source_sha256')})
        new_hashes = {rel: sha(raw) for rel, raw in data.items()}
        report = {'previous_generation': old_m.get('generation'), 'generation': generation,
                  'source_files': {rel: {'old': old_hashes.get(rel), 'new': new_hashes.get(rel)}
                    for rel in sorted(set(old_hashes) | set(new_hashes))
                    if old_hashes.get(rel) != new_hashes.get(rel)},
                  'entries': [], 'preserved_translations': 0, 'existing_pending': 0,
                  'new_pending': 0, 'warnings': [], 'validation': 'passed'}
        incoming_by_id = {r['id']: r for r in incoming}
        require(len(incoming_by_id) == len(incoming), 'Duplicate incoming IDs')
        for r in incoming:
            prior = old.get(r['id'])
            kind = 'added'
            if prior:
                before, after = immutable(prior), immutable(r)
                before.pop('row'); after.pop('row')
                if before == after:
                    r['PTBR'] = prior['PTBR']
                    kind = 'moved' if prior['row'] != r['row'] else 'unchanged'
                    report['preserved_translations'] += bool(prior['PTBR'])
                    report['existing_pending'] += not bool(prior['PTBR'])
                else:
                    kind = 'modified'
            if kind in ('modified', 'added'):
                report['new_pending'] += 1
            if kind != 'unchanged':
                report['entries'].append({'id': r['id'], 'classification': kind,
                    'previous': prior, 'current': r, 'batch': owners.get(r['id'])})
        for key in old.keys() - incoming_by_id.keys():
            report['entries'].append({'id': key, 'classification': 'removed',
                'previous': old[key], 'current': None, 'batch': owners[key]})
        updated = {name: [incoming_by_id[x['id']] for x in rs if x['id'] in incoming_by_id]
                   for name, rs in batches.items()}
        updated = {n: rs for n, rs in updated.items() if rs}
        new = [r for r in incoming if r['id'] not in old]
        require(initial or batch_size is None, 'Batch size can be set only on initial extract')
        cap = old_m.get('batch_size', batch_size if batch_size is not None else self.config['batch_size'])
        require(type(cap) is int and 1 <= cap <= 10000, 'Batch size must be between 1 and 10000')
        last_num = max([int(n[6:10]) for n in batches] or [0])
        if updated:
            last = sorted(updated)[-1]
            available = cap - len(updated[last])
            updated[last].extend(new[:available]); new = new[available:]
        while new:
            last_num += 1
            name = f'batch-{last_num:04d}.jsonl'
            updated[name], new = new[:cap], new[cap:]
        m = {'schema': 1, 'game': self.config['game'], 'deployment_path': DEPLOY,
             'generation': generation, 'source_sha256': sha(encoded({rel: sha(raw) for rel, raw in data.items()})), 'source_hashes': new_hashes,
             'source_language': 'zh-Hans',
             'catalog_sha256': sha(encoded(accepted)), 'record_count': len(incoming),
             'batch_size': cap, 'batches': list(sorted(updated)),
             'shape_sha256': shape_hash}
        updates = {'EN/' + rel: raw for rel, raw in data.items()}
        updates.update({MANIFEST: encoded(m), CATALOG: encoded(accepted)})
        for name in set(batches) | set(updated):
            updates[TRANS + name] = lines(updated[name]) if name in updated else None
        owners_new = {r['id']: n for n, rs in updated.items() for r in rs}
        for e in report['entries']:
            e['batch'] = owners_new.get(e['id'], e['batch'])
        report['counts'] = dict(collections.Counter(e['classification'] for e in report['entries']))
        report['counts']['unchanged'] = len(incoming) - sum(e['classification'] != 'removed'
                                                         for e in report['entries'])
        report['affected_batches'] = sorted(n for n in set(batches) | set(updated)
            if lines(batches.get(n, [])) != lines(updated.get(n, [])))
        updates[WORK + 'reports/sync-latest.json'] = encoded(report)
        summary = '# Sincronização de fontes\n\n' + '\n'.join(
            f'- {k}: {v}' for k, v in report['counts'].items())
        summary += '\n\nRevise entradas adicionadas/modificadas. O relatório JSON contém textos anteriores, '
        summary += 'traduções históricas e IDs. Consulte status para saber se este relatório ainda corresponde à geração ativa.\n'
        updates[WORK + 'reports/sync-latest.md'] = summary.encode('utf-8')
        if dry:
            return {'status': 'dry-run', **report}
        self.current_guard(expected)
        report_id = self.store.commit(updates, expected)
        return {'status': 'extracted' if initial else 'synchronized', 'transaction': report_id,
                'records': len(incoming), 'batches': len(updated), **report}

    def apply(self, payload, replace=False):
        expected = self.expectations()
        m, records, batches, owners = self.workspace()
        require(payload.get('generation') == m['generation'], 'Wrong source generation')
        entries = payload.get('entries')
        require(isinstance(entries, list) and entries, 'entries must be a nonempty array')
        ids = [x.get('id') for x in entries]
        require(len(ids) == len(set(ids)) and set(ids) <= records.keys(), 'Duplicate/unknown payload IDs')
        applied, rejected, changed = [], [], set()
        for e in entries:
            try:
                require(set(e) == {'id', 'PTBR'}, 'Payload may change only id/PTBR')
                r = records[e['id']]
                validate_text(r['ZH_CN'], e['PTBR'])
                require(bool(e['PTBR']), 'Use nonempty PTBR; blank means pending')
                require(replace or not r['PTBR'] or r['PTBR'] == e['PTBR'],
                        'Existing translation protected; use --replace after review')
                if r['PTBR'] != e['PTBR']:
                    r['PTBR'] = e['PTBR']; changed.add(owners[e['id']])
                applied.append(e['id'])
            except (ValueError, KeyError) as err:
                rejected.append({'id': e.get('id'), 'reason': str(err)})
        self.current_guard(expected)
        tx = self.store.commit({TRANS + n: lines(batches[n]) for n in changed}, expected)
        return {'applied': applied, 'rejected': rejected, 'transaction': tx}

    def status(self):
        m, records, batches, _ = self.workspace()
        done = sum(bool(r['PTBR']) for r in records.values())
        build = self.root / WORK / 'build-manifest.json'
        stale = (not build.exists() or load(build).get('translation_fingerprint') != self.fingerprint(records)
                 or load(build).get('generation') != m['generation']
                 or load(build).get('toolchain_sha256') != sha(canonical((self.root / WORK / 'toolchain.json').read_bytes())))
        first = next((r for n in sorted(batches) for r in batches[n] if not r['PTBR']), None)
        report = self.root / WORK / 'reports/sync-latest.json'
        return {'generation': m['generation'], 'total': len(records), 'completed': done,
                'pending': len(records) - done, 'batches': len(batches), 'output_stale': stale,
                'next_id': first['id'] if first else None,
                'latest_diff_matches_generation': report.exists() and load(report)['generation'] == m['generation'],
                'storage': self.store.stats()}

    def build(self):
        expected = self.expectations([WORK + 'build-manifest.json', 'PTBR/' + PLUGIN, 'PTBR/' + DELTA])
        m, records, _, _ = self.workspace()
        pending = sum(not r['PTBR'] for r in records.values())
        require(not pending, f'Build blocked: {pending} entries pending')
        hashes = {name: m['source_hashes']['TextAsset/' + name + '.json'] for name in self.shape['tables']}
        delta = make_delta(records.values(), hashes)
        for name, spec in delta['tables'].items():
            if (self.root / 'EN').exists():
                raw = safe(self.root, 'EN/TextAsset/' + name + '.json').read_bytes()
                apply_table(raw, name, spec)
        outputs = {PLUGIN: safe(self.root, WORK + 'runtime/CultivationPtBr.dll').read_bytes(),
                   DELTA: encoded(delta)}
        output_root = self.root / 'PTBR'
        if output_root.exists():
            for p in output_root.rglob('*'):
                rel = p.relative_to(output_root).as_posix()
                safe(self.root, 'PTBR/' + rel)
                require(not p.is_file() or rel in outputs, 'Unexpected PTBR file: ' + rel)
        receipt = {'schema': 1, 'generation': m['generation'], 'source_sha256': m['source_sha256'],
                   'translation_fingerprint': self.fingerprint(records), 'record_count': len(records),
                   'output': {rel: sha(raw) for rel, raw in outputs.items()},
                   'game_version': self.shape['game_version'], 'target_language': 'Português (Brasil)',
                   'toolchain_sha256': sha(canonical((self.root / WORK / 'toolchain.json').read_bytes()))}
        self.current_guard(expected)
        changes = {'PTBR/' + rel: raw for rel, raw in outputs.items()}
        changes[WORK + 'build-manifest.json'] = encoded(receipt)
        tx = self.store.commit(changes, expected)
        return {'status': 'built', 'transaction': tx, 'output': receipt['output']}

    def verify_output(self):
        m, records, _, _ = self.workspace()
        require(all(r['PTBR'] for r in records.values()), 'Incomplete translations')
        receipt = load(self.root / WORK / 'build-manifest.json')
        require(receipt['schema'] == 1 and receipt['generation'] == m['generation']
                and receipt['source_sha256'] == m['source_sha256']
                and receipt['record_count'] == len(records)
                and receipt['translation_fingerprint'] == self.fingerprint(records)
                and receipt['toolchain_sha256'] == sha(canonical((self.root / WORK / 'toolchain.json').read_bytes())),
                'Stale/forged build manifest; explicit complete build required')
        output_root = safe(self.root, 'PTBR')
        files = {}
        for p in output_root.rglob('*'):
            rel = p.relative_to(output_root).as_posix()
            safe(self.root, 'PTBR/' + rel)
            if p.is_file():
                files[rel] = digest(p)
        require(files == receipt['output'] and set(files) == {PLUGIN, DELTA}, 'Output inventory/hash mismatch')
        hashes = {name: m['source_hashes']['TextAsset/' + name + '.json'] for name in self.shape['tables']}
        require(digest(output_root / PLUGIN) == digest(self.root / WORK / 'runtime/CultivationPtBr.dll')
                and (output_root / DELTA).read_bytes() == encoded(make_delta(records.values(), hashes)),
                'Output differs from verified plugin or translation delta')
        return receipt

    def doctor(self, target='linux-arm64'):
        self.integrity()
        require(sys.version_info >= (3, 10), 'Missing runtime: Python 3.10+ required')
        if target == 'linux-arm64':
            require(platform.system() == 'Linux' and platform.machine().lower() in ('aarch64', 'arm64'),
                    'Unsupported architecture: expected Linux ARM64; use --target host only for developer tests')
        raw = b'{"DialogueInfos":[{"Id":7,"Chinese":"a\t{0}","Extra":42}]}'
        fixture = {'tables': {'DialogueInfo': ['Chinese']}}
        rows = catalog({'DialogueInfo': raw}, fixture)
        require(rows[0]['ZH_CN'] == 'a\t{0}', 'Malformed fixture: unexpected text')
        rows[0]['PTBR'] = 'á {0}'
        delta = make_delta(rows, {'DialogueInfo': sha(raw)})
        rebuilt = apply_table(raw, 'DialogueInfo', delta['tables']['DialogueInfo'])
        require(rebuilt == {'DialogueInfos': [{'Id': 7, 'Chinese': 'á {0}', 'Extra': 42}]},
                'Fixture changed protected structure')
        catalog_present = (self.root / MANIFEST).is_file()
        if catalog_present:
            self.workspace()
        return {'status': 'ok', 'catalog': 'validated' if catalog_present else 'local-import-required', 'target': target, 'architecture': platform.machine(),
                'python': platform.python_version(), 'dependencies': 'standard-library-only',
                'fixture_roundtrip': 'passed', 'read_only': True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('extract', 'sync', 'update-sources', 'diff'):
        p = sub.add_parser(name)
        g = p.add_mutually_exclusive_group()
        g.add_argument('--game-root'); g.add_argument('--source-file'); g.add_argument('--source-root')
        p.add_argument('--dry-run', action='store_true')
        if name == 'extract':
            p.add_argument('--batch-size', type=int)
    for name in ('check', 'status', 'resume', 'build', 'verify-output'):
        sub.add_parser(name)
    p = sub.add_parser('apply'); p.add_argument('payload', type=Path); p.add_argument('--replace', action='store_true')
    p = sub.add_parser('doctor'); p.add_argument('--target', choices=['host', 'linux-arm64'], default='linux-arm64')
    p = sub.add_parser('gc'); p.add_argument('--dry-run', action='store_true')
    p = sub.add_parser('recover'); p.add_argument('--rollback')
    args = parser.parse_args(argv)
    try:
        project = Project(args.root)
        project.integrity()
        cmd = args.command
        writable = cmd in ('extract', 'sync', 'update-sources', 'apply', 'build', 'recover') or (cmd == 'gc' and not args.dry_run)
        dry = getattr(args, 'dry_run', False)
        import contextlib
        with project.store.lock(recover=cmd == 'recover') if writable and not dry else contextlib.nullcontext():
            if cmd == 'doctor':
                result = project.doctor(args.target)
            elif cmd in ('check', 'status', 'resume'):
                result = project.status()
            elif cmd in ('extract', 'sync', 'update-sources', 'diff'):
                if cmd == 'diff' and not any([args.game_root, args.source_file, args.source_root]):
                    result = load(project.root / WORK / 'reports/sync-latest.json')
                else:
                    game = args.game_root
                    if cmd in ('extract', 'update-sources') and not any([game, args.source_file, args.source_root]):
                        game = project.discover()
                    data, rows = project.candidate(game, args.source_file, args.source_root)
                    if cmd == 'update-sources' and not (project.root / MANIFEST).exists():
                        cmd = 'extract'
                    result = project.synchronize(data, rows, cmd == 'extract', dry or cmd == 'diff',
                                                 getattr(args, 'batch_size', None))
            elif cmd == 'apply':
                result = project.apply(load(args.payload), args.replace)
            elif cmd == 'build':
                result = project.build()
            elif cmd == 'verify-output':
                result = project.verify_output()
            elif cmd == 'gc':
                result = project.store.gc(args.dry_run)
            elif cmd == 'recover':
                result = {'recovered': project.store.recover(args.rollback)}
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 2 if isinstance(result, dict) and result.get('rejected') else 0
    except (ValueError, KeyError, OSError, UnicodeError) as err:
        print(json.dumps({'error': str(err)}, ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
