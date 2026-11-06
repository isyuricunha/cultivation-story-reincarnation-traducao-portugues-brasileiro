import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from native import DELTA, DEPLOY, PLUGIN, catalog, parse, sha
from storage import Store, encoded
from toolkit import MANIFEST, ROOT, TRANS, WORK, Project


class Sandbox(unittest.TestCase):
    def setUp(self):
        (ROOT / '.local').mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=ROOT / '.local')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for relative in ['.gitattributes', WORK + 'toolchain.json', WORK + 'runtime-support.json']:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, path)
        receipt = json.loads((ROOT / WORK / 'toolchain.json').read_bytes())
        for relative in receipt['files']:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, path)
        self.p = Project(self.root)
        self.p.shape['tables'] = {'DialogueInfo': ['Chinese']}

    def candidate(self, text='Fixture {0}', reverse=False):
        rows = [{'Id': 7, 'Chinese': text, 'Other': 19}, {'Id': 8, 'Chinese': 'Other'}]
        if reverse:
            rows.reverse()
        raw = encoded({'DialogueInfos': rows})
        data = {DEPLOY: b'fixture bundle ' + raw, 'TextAsset/DialogueInfo.json': raw}
        return data, catalog({'DialogueInfo': raw}, self.p.shape)

    def init(self):
        self.p.synchronize(*self.candidate(), initial=True)

    def payload(self, values):
        manifest, _, _, _ = self.p.workspace()
        return {'generation': manifest['generation'],
                'entries': [{'id': key, 'PTBR': value} for key, value in values.items()]}

    def complete(self):
        _, rows, _, _ = self.p.workspace()
        result = self.p.apply(self.payload({key: row['ZH_CN'] + ' á' for key, row in rows.items()}))
        self.assertFalse(result['rejected'])


class ToolkitTests(Sandbox):
    def test_pending_stale_and_forged_output(self):
        self.init()
        with self.assertRaisesRegex(ValueError, 'pending'):
            self.p.build()
        self.assertFalse((self.root / 'PTBR').exists())
        self.complete()
        self.p.build()
        self.p.verify_output()
        path = self.root / 'PTBR' / DELTA
        path.write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'hash'):
            self.p.verify_output()
        self.p.build()
        self.p.apply(self.payload({'DialogueInfo/7/Chinese': 'Alterado {0}'}), replace=True)
        with self.assertRaisesRegex(ValueError, 'Stale'):
            self.p.verify_output()

    def test_sync_reorder_review_and_dry_run(self):
        self.init()
        self.complete()
        old = (self.root / MANIFEST).read_bytes()
        preview = self.p.synchronize(*self.candidate(reverse=True), dry=True)
        self.assertEqual(preview['counts']['moved'], 2)
        self.assertEqual((self.root / MANIFEST).read_bytes(), old)
        self.p.synchronize(*self.candidate(reverse=True))
        self.assertEqual(self.p.status()['completed'], 2)
        report = self.p.synchronize(*self.candidate('Changed {0}', reverse=True))
        self.assertEqual(report['counts']['modified'], 1)
        self.assertEqual(report['entries'][0]['previous']['PTBR'], 'Fixture {0} á')
        self.assertEqual(self.p.status()['pending'], 1)

    def test_apply_protects_tokens_and_translated_values(self):
        self.init()
        bad = self.p.apply(self.payload({'DialogueInfo/7/Chinese': 'Sem variável'}))
        self.assertEqual(len(bad['rejected']), 1)
        self.complete()
        denied = self.p.apply(self.payload({'DialogueInfo/7/Chinese': 'Alterado {0}'}))
        self.assertEqual(len(denied['rejected']), 1)
        self.assertEqual(self.p.status()['completed'], 2)

    def test_preflight_normalization_and_binary_tampering(self):
        self.init()
        metadata = self.root / WORK / 'project.json'
        original = metadata.read_bytes()
        metadata.write_bytes(original.replace(b'\n', b'\r\n'))
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), 'add', '.gitattributes', WORK + 'project.json'],
                       check=True, capture_output=True)
        git_bytes = subprocess.check_output(['git', '-C', str(self.root), 'show', ':' + WORK + 'project.json'])
        self.assertEqual(git_bytes, original)
        self.p.doctor('host')
        with mock.patch('platform.machine', return_value='aarch64'), mock.patch('platform.system', return_value='Linux'):
            self.p.doctor()
        metadata.write_bytes(original.replace(b'500', b'501'))
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.p.doctor('host')
        metadata.write_bytes(original)
        dll = self.root / WORK / 'runtime/CultivationPtBr.dll'
        dll.write_bytes(dll.read_bytes() + b'x')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.p.doctor('host')

    def test_source_tamper_and_duplicate_ids(self):
        self.init()
        source = self.root / 'EN' / DEPLOY
        source.write_bytes(source.read_bytes() + b'x')
        with self.assertRaisesRegex(ValueError, 'Local EN'):
            self.p.workspace()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            parse(b'{"Id":7,"Id":8}')

    def test_storage_500_tiny_updates(self):
        store = Store(self.root, count=5, budget=128 * 1024)
        files = {TRANS + f'batch-{i:04}.jsonl': b'x' * 8192 for i in range(101)}
        with store.lock():
            store.commit(files)
            for i in range(500):
                path = TRANS + f'batch-{i % 101:04}.jsonl'
                store.commit({path: str(i).encode()})
        stats = store.stats()
        self.assertLessEqual(len(store.receipts()), 5)
        self.assertLessEqual(stats['bytes'], 128 * 1024)
