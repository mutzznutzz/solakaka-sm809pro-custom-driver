"""Robin's reported regressions. Uses isolated profiles and mocked HID only."""
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from app.dpi_state import wire_config
from app import controller, profile_store, macro_store
from sm809pro import actions as A, protocol as P, device


class FeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patches = [patch.object(controller.DeviceController, 'start', lambda self: None),
                        patch.object(device, 'hid', None),
                        patch.object(profile_store, 'default_path', lambda: self.tmp.name + '/profiles.json'),
                        patch.object(macro_store, 'default_path', lambda: self.tmp.name + '/macros.json')]
        for p in self.patches:
            p.start()
        from app.main_window import MainWindow
        self.w = MainWindow()
        self.calls = []
        self.w.ctrl.call = lambda method, *a, **kw: self.calls.append((method, a, kw))

    def tearDown(self):
        self.w.ctrl.shutdown()
        if self.w.tray:
            self.w.tray.hide()
        self.w.hide()
        self.w.deleteLater()
        self.app.processEvents()
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_sparse_dpi_round_trip_and_live_highlight(self):
        panel = self.w.dpi_panel
        panel.set_values([400, 800, 1200, 1600, 2400, 3200, 6400, 8000], enabled_indices=[0, 2, 4, 6])
        panel.set_active_stage(4)
        panel._emit_apply()
        saved = self.w._current_config['dpi']
        self.assertEqual(saved['enabled_indices'], [0, 2, 4, 6])
        self.assertEqual(wire_config(saved)[0], [400, 1200, 2400, 6400])
        self.assertEqual(wire_config(saved)[2], 2)
        self.w._seed_panels(self.w._current_config)
        self.w._on_dpi_push(3)
        self.assertEqual(panel._selected, 6)
        self.assertEqual(self.w.topbar.dpi_readout.text(), '6400')
        self.assertEqual(panel._enabled_indices(), [0, 2, 4, 6])
        disk = profile_store.ProfileStore(self.tmp.name + '/profiles.json')
        self.assertEqual(disk.get(disk.active_id)['config']['dpi']['enabled_indices'], [0, 2, 4, 6])

    def test_old_dpi_profiles_remain_compatible(self):
        self.assertEqual(wire_config(dict(values=[400, 800, 1600], enabled_count=2, selected=1)),
                         ([400, 800], [[255,255,255], [255,255,255]], 1))

    def test_wheel_remap_preserved_across_buttons_and_profile_apply(self):
        wheel = [(0x70, 0, 4), A.BTN['wheel_down']]
        self.w._apply_wheel(wheel)
        self.w._apply_buttons(self.w.buttons_panel.bindings())
        self.assertEqual(self.calls[-1][2]['wheel_codes'], [list(c) for c in wheel])
        cfg = self.w._current_config.copy()
        self.w.apply_profile(cfg, force=True)
        self.assertEqual(self.calls[-1][2]['wheel_codes'], [list(c) for c in wheel])
        dev = device.SM809Pro()
        packets = []
        dev._send_packet = lambda p: packets.append(bytes(p)) or True
        self.assertTrue(dev.set_keys(A.default_button_codes(), wheel_codes=wheel))
        self.assertEqual(packets[-1][-6:], bytes(sum((list(c) for c in wheel), [])))
        self.assertEqual(len(self.w.buttons_panel.rows), 16)

    def test_wired_zero_is_usb_power_without_alert(self):
        self.w._on_connected(dict(connection='wired', configurable=False))
        self.w._on_battery(0)
        self.assertEqual(self.w.topbar.battery.text(), 'USB powered')
        self.assertFalse(self.w.alert_overlay.isVisible())
        self.w._on_connected(dict(connection='2.4GHz', configurable=False))
        self.w._on_battery(10)
        self.assertTrue(self.w.alert_overlay.isVisible())

    def test_receiver_809f_is_wireless(self):
        self.assertIn(0x809f, P.WIRELESS_PIDS)
        fake = type('Hid', (), {'enumerate': staticmethod(lambda vid, pid: [dict(vendor_id=P.VID, product_id=0x809f, path=b'test')])})()
        with patch.object(device, 'hid', fake):
            candidates = device.detect_modes()
        self.assertTrue(any(c['connection'] == '2.4GHz' for c in candidates))

    def test_polling_feedback_is_immediate_and_not_false_confirmation(self):
        self.w._overlay_enabled = True
        self.w._pending_rates = [(500, False)]
        self.w._apply_polling(1000)
        self.assertTrue(self.w.overlay.isVisible())
        self.assertIn('APPLYING', self.w.overlay._lay.itemAt(0).widget().text())
        self.w._on_command_done('set_polling_rate', True)
        self.assertIn('APPLYING', self.w.overlay._lay.itemAt(0).widget().text())
        self.w._on_command_done('set_polling_rate', False)
        self.assertIn("COULDN'T", self.w.overlay._lay.itemAt(0).widget().text())

    def test_lighting_is_embedded_with_presets_only(self):
        panel = self.w.lighting_panel
        self.assertIs(panel, self.w.performance_panel.lighting_panel)
        self.assertIs(self.w.stack.widget(3), self.w.performance_panel)
        self.assertEqual(panel.mode_combo.findData(100), -1)
        panel.set_state(8, (17, 34, 51), custom=True)
        self.assertFalse(panel.is_custom)
        self.assertEqual(panel.mode_combo.currentData(), 8)
        panel.mode_combo.setCurrentIndex(panel.mode_combo.findData(9))
        self.assertEqual(self.calls[-1][0:2], ('set_lighting', (9,)))
        self.assertFalse(self.w._current_config['lighting']['custom'])


if __name__ == '__main__':
    unittest.main()
