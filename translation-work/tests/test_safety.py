
from test_toolkit import Sandbox
from consent import ATTESTATION, validate
from native import DEPLOY, apply_table, sha
from storage import Store


class SafetyTests(Sandbox):
    def test_contributor_permission(self):
        commit = {'sha': 'fixture', 'author': {'login': 'contributor'}}
        with self.assertRaisesRegex(ValueError, 'Explicit'):
            validate('', 'contributor', [commit])
        self.assertTrue(validate(ATTESTATION, 'contributor', [commit]))
        with self.assertRaisesRegex(ValueError, 'co-contributor'):
            validate(ATTESTATION, 'another-user', [commit])

    def test_gc_protects_interrupted_operation(self):
        store = Store(self.root)
        a, b = 'translation-work/a.json', 'translation-work/b.json'
        with store.lock():
            store.commit({a: b'before', b: b'also before'})
            def interrupt(_):
                raise RuntimeError('fixture interruption')
            with self.assertRaisesRegex(RuntimeError, 'interruption'):
                store.commit({a: b'after', b: b'also after'}, fault=interrupt)
            with self.assertRaisesRegex(ValueError, 'Pending'):
                store.gc(dry=True)
            self.assertEqual(len(store.recover()), 1)
            self.assertEqual((self.root / a).read_bytes(), b'before')
            self.assertEqual((self.root / b).read_bytes(), b'also before')
            self.assertEqual(store.stats()['protected'], 0)

    def test_native_delta_rejects_malformed_and_wrong_address(self):
        raw = b'{"DialogueInfos":[{"Id":7,"Chinese":"a"}]}'
        with self.assertRaisesRegex(ValueError, 'checksum'):
            apply_table(raw, 'DialogueInfo', {'sha256': 'incorrect', 'rows': {}})
        with self.assertRaisesRegex(ValueError, 'Unknown native ID'):
            apply_table(raw, 'DialogueInfo', {'sha256': sha(raw), 'rows': {'8': {}}})
        with self.assertRaisesRegex(ValueError, 'Invalid native field'):
            apply_table(raw, 'DialogueInfo', {'sha256': sha(raw), 'rows': {'7': {'Id': 'x'}}})

    def test_restore_missing_en_without_touching_catalog(self):
        self.init()
        original = self.p.status()['generation']
        (self.root / 'EN' / DEPLOY).unlink()
        data, rows = self.candidate()
        self.assertEqual(self.p.synchronize(data, rows, dry=True)['status'], 'dry-run')
        self.assertFalse((self.root / 'EN' / DEPLOY).exists())
        result = self.p.synchronize(data, rows)
        self.assertEqual(result['status'], 'sources-restored')
        self.assertEqual(self.p.status()['generation'], original)
        self.assertEqual((self.root / 'EN' / DEPLOY).read_bytes(), data[DEPLOY])
