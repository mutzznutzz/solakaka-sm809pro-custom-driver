"""Isolated GUI integration for undo, restore, credits and diagnostics."""
import test_feedback_regression as fixtures
from app import backup
from unittest.mock import patch
from PySide6.QtWidgets import QMessageBox
import pathlib
import unittest


class NewFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.FeedbackTests.setUpClass()
        cls.app = fixtures.FeedbackTests.app

    setUp = fixtures.FeedbackTests.setUp
    tearDown = fixtures.FeedbackTests.tearDown

    def test_undo_restores_wheel_without_changing_other_buttons(self):
        original = self.w.buttons_panel.bindings()
        self.w._apply_wheel([(0x70, 0, 4), (0x10, 0x40, 0)])
        self.assertTrue(self.w.undo_btn.isEnabled())
        self.w._undo_setting()
        self.assertEqual(self.w.buttons_panel._wheel, [(0x10, 0x20, 0), (0x10, 0x40, 0)])
        self.assertEqual(self.w.buttons_panel.bindings(), original)
        self.assertFalse(self.w.undo_btn.isEnabled())

    def test_auto_profile_edit_and_undo_do_not_overwrite_base(self):
        base = self.w.profiles.active_id
        game = self.w.profiles.add('Game')
        self.w._apply_by_id(game['id'])
        self.w._apply_polling(1000)
        self.assertEqual(self.w.profiles.get(game['id'])['config']['polling_hz'], 1000)
        self.assertEqual(self.w.profiles.get(base)['config']['polling_hz'], 500)
        self.w._undo_setting()
        self.assertEqual(self.w.profiles.get(game['id'])['config']['polling_hz'], 500)
        self.assertEqual(self.w.profiles.active_id, base)

    def test_restore_refreshes_all_stores_preferences_and_panels(self):
        self.w._apply_polling(1000)
        self.w.profiles.set_setting('overlay', True)
        macro = self.w.store.add('Saved macro')
        saved = backup.snapshot(self.w.profiles, self.w.store)
        self.w._apply_polling(125)
        self.w.store.delete(macro['id'])
        recovery = backup.restore(saved, self.w.profiles, self.w.store)
        self.w._reload_restored_settings()
        self.assertTrue(recovery.exists())
        self.assertEqual(self.w.performance_panel.polling.value(), 1000)
        self.assertEqual(self.w.store.get(macro['id'])['name'], 'Saved macro')
        self.assertTrue(self.w._overlay_enabled)
        self.assertFalse(self.w.undo_btn.isEnabled())

    def test_diagnostics_never_open_hid_or_include_config_secrets(self):
        modes = [dict(vid=0x04f3, pid=0x809f, connection='2.4GHz', configurable=True,
                      devs=[dict(bus_type=1, path=b'secret-raw-path', serial_number='secret-serial')])]
        with patch('sm809pro.device.detect_modes', return_value=modes):
            self.w._refresh_diagnostics()
        report = self.w.about_panel.report.toPlainText()
        self.assertIn('04F3:809F', report)
        self.assertNotIn('secret', report)
        self.assertEqual(self.calls, [])
        self.assertIn('Robin Luxton at MutzNutz Media and Design', self.w.about_panel.credits.text())
        self.assertIn('lacno29', self.w.about_panel.credits.text())

    def test_export_dialog_saves_a_complete_portable_file(self):
        path = pathlib.Path(self.tmp.name) / 'all-settings'
        with patch('app.main_window.QFileDialog.getSaveFileName', return_value=(str(path), '')), patch('app.main_window.QMessageBox.information'):
            self.w._backup_all()
        saved = backup.read(str(path) + '.sm809backup')
        self.assertEqual(saved['profiles']['active'], self.w.profiles.active_id)
        self.assertEqual(self.calls, [])

    def test_cancelled_restore_does_not_replace_settings(self):
        path = pathlib.Path(self.tmp.name) / 'backup.sm809backup'
        backup.write(path, backup.snapshot(self.w.profiles, self.w.store))
        self.w._apply_polling(1000)
        self.calls.clear()
        with patch('app.main_window.QFileDialog.getOpenFileName', return_value=(str(path), '')), patch('app.main_window.QMessageBox.question', return_value=QMessageBox.Cancel):
            self.w._restore_all()
        self.assertEqual(self.w._current_config['polling_hz'], 1000)
        self.assertEqual(self.calls, [])

    def test_restore_dialog_updates_settings_after_confirmation(self):
        path = pathlib.Path(self.tmp.name) / 'backup.sm809backup'
        backup.write(path, backup.snapshot(self.w.profiles, self.w.store))
        self.w._apply_polling(1000)
        with patch('app.main_window.QFileDialog.getOpenFileName', return_value=(str(path), '')), patch('app.main_window.QMessageBox.question', return_value=QMessageBox.Yes), patch('app.main_window.QMessageBox.information'):
            self.w._restore_all()
        self.assertEqual(self.w._current_config['polling_hz'], 500)
        self.assertFalse(self.w.undo_btn.isEnabled())

    def test_factory_reset_clears_target_history_and_preserves_manual_base(self):
        base = self.w.profiles.active_id
        self.w._apply_polling(125)
        game = self.w.profiles.add('Game')
        self.w._apply_by_id(game['id'])
        self.w._apply_polling(1000)
        with patch('app.main_window.QMessageBox.exec', return_value=QMessageBox.Yes):
            self.w._confirm_reset()
        self.assertEqual(self.w.profiles.get(base)['config']['polling_hz'], 125)
        self.assertEqual(self.w.profiles.get(game['id'])['config']['polling_hz'], 500)
        self.assertFalse(self.w.undo_btn.isEnabled())


if __name__ == '__main__':
    unittest.main()
