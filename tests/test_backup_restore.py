"""Backups must round-trip all state and leave current data intact on failure."""
import copy
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from app import backup
from app.profile_store import ProfileStore
from app.macro_store import MacroStore
from app.persistence import atomic_json


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.profiles = ProfileStore(str(self.root / 'profiles.json'))
        self.macros = MacroStore(str(self.root / 'macros.json'))
        macro = self.macros.add('Example')
        self.macros.set_events(macro['id'], [dict(type='key', keycode=4, down=True, next_delay=20), dict(type='key', keycode=4, down=False)])
        game = self.profiles.add('Game', match_rules=[{'exe': 'game.exe'}])
        game['config']['buttons'][0] = dict(macro=macro['id'], playmode=1, repeat=0)
        game['config']['wheel'] = [[0x70, 0, 5], [0x10, 0x40, 0]]
        game['config']['dpi'].update(enabled_indices=[0, 2, 4], enabled_count=3, selected=2)
        self.profiles.set_active(game['id'])
        self.profiles.set_setting('overlay', True)
        self.profiles.set_setting('auto_switch', True)
        self.profiles.set_setting('overlay_scale', 125)
        self.original = backup.snapshot(self.profiles, self.macros)

    def tearDown(self):
        self.tmp.cleanup()

    def test_complete_round_trip_with_recovery_copy(self):
        path = self.root / 'portable.sm809backup'
        backup.write(path, self.original)
        data = backup.read(path)
        self.profiles.rename(self.profiles.active_id, 'Changed')
        self.macros.add('Another')
        before = backup.snapshot(self.profiles, self.macros)
        recovery = backup.restore(data, self.profiles, self.macros)
        after = backup.snapshot(self.profiles, self.macros)
        self.assertEqual(after['profiles'], self.original['profiles'])
        self.assertEqual(after['macros'], self.original['macros'])
        self.assertEqual(backup.read(recovery)['profiles'], before['profiles'])
        self.assertEqual(backup.read(recovery)['macros'], before['macros'])
        self.assertEqual(ProfileStore(self.profiles.path).active_id, self.original['profiles']['active'])

    def test_bad_backup_does_not_change_existing_files(self):
        old = pathlib.Path(self.profiles.path).read_bytes()
        for mutate in [lambda b: b.update(version=99),
                       lambda b: b['profiles'].update(active='missing'),
                       lambda b: b['profiles']['profiles'][0]['config']['buttons'].pop(),
                       lambda b: b['profiles']['profiles'][0]['config']['dpi'].update(enabled_count=10**20),
                       lambda b: b['profiles']['settings'].update(overlay_scale='bad'),
                       lambda b: b['macros'][0]['events'][0].update(type='execute')]:
            broken = copy.deepcopy(self.original)
            mutate(broken)
            with self.assertRaises(backup.BackupError):
                backup.restore(broken, self.profiles, self.macros)
            self.assertEqual(pathlib.Path(self.profiles.path).read_bytes(), old)

    def test_second_file_failure_rolls_back_first_and_keeps_recovery(self):
        before = [pathlib.Path(s.path).read_bytes() if pathlib.Path(s.path).exists() else None for s in (self.profiles, self.macros)]
        changed = copy.deepcopy(self.original)
        changed['profiles']['profiles'][0]['name'] = 'Restored name'
        def fail_second(path, content):
            if str(path) == self.macros.path:
                raise OSError('Simulated write failure')
            return atomic_json(path, content)
        with patch('app.backup.atomic_json', side_effect=fail_second):
            with self.assertRaises(OSError):
                backup.restore(changed, self.profiles, self.macros)
        self.assertEqual([pathlib.Path(s.path).read_bytes() for s in (self.profiles, self.macros)], before)
        self.assertEqual(len(list((self.root / 'backups').glob('*.sm809backup'))), 1)

    def test_atomic_autosave_keeps_previous_file_on_failure(self):
        old = pathlib.Path(self.profiles.path).read_bytes()
        with patch('app.persistence.os.replace', side_effect=OSError('denied')):
            self.assertFalse(self.profiles.save())
        self.assertEqual(pathlib.Path(self.profiles.path).read_bytes(), old)
        self.assertIn('denied', self.profiles.last_save_error)
        self.assertFalse(list(self.root.glob('*.tmp')))

    def test_truncated_oversized_and_non_finite_files_are_rejected(self):
        path = self.root / 'bad.sm809backup'
        for raw in [b'{', b' ' * (backup.MAX_BYTES + 1), b'{"version":NaN}']:
            path.write_bytes(raw)
            with self.assertRaises(backup.BackupError):
                backup.read(path)

    def test_snapshot_is_detached_from_live_data(self):
        self.profiles.active()['config']['buttons'][0] = [255, 255, 255]
        self.assertIsInstance(self.original['profiles']['profiles'][-1]['config']['buttons'][0], dict)


if __name__ == '__main__':
    unittest.main()
