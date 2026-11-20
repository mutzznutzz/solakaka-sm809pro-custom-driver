"""Transport detection must never mistake an Elan laptop touchpad for a mouse."""
import pathlib
import sys
import time
import unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from sm809pro import device, protocol as P


def interface(pid, product='SM809Pro', bus=1, vid=P.VID):
    return dict(vendor_id=vid, product_id=pid, product_string=product,
                bus_type=bus, usage_page=0x0a, path=b'fake#Col05')


def detect(devices):
    class Hid:
        @staticmethod
        def enumerate(vid=0, pid=0):
            return [d for d in devices if (not vid or d['vendor_id'] == vid)
                    and (not pid or d['product_id'] == pid)]
    with patch.object(device, 'hid', Hid):
        return device.detect_modes()


class TransportTests(unittest.TestCase):
    def test_touchpad_only_is_not_a_mouse(self):
        self.assertEqual(detect([interface(0x3282, 'HIDI2C Device', 3)]), [])

    def test_touchpad_cannot_override_receiver(self):
        modes = detect([interface(0x3282, 'HIDI2C Device', 3), interface(0x809f)])
        self.assertEqual(len(modes), 1)
        self.assertEqual(device.choose_mode(modes)['connection'], '2.4GHz')

    def test_unrelated_usb_elan_is_excluded(self):
        self.assertEqual(detect([interface(0x9999, 'Other Elan device', 1)]), [])

    def test_cable_has_priority_over_receiver(self):
        modes = detect([interface(0x809f), interface(0x809e)])
        self.assertEqual(device.choose_mode(modes)['connection'], 'wired')

    def test_real_bluetooth_requires_transport_evidence(self):
        bt = interface(0x0270, bus=2)
        bt['usage_page'] = 1
        mode = detect([bt])[0]
        self.assertEqual(mode['connection'], 'bluetooth')
        self.assertFalse(mode['configurable'])

    def test_unknown_named_usb_mouse_is_not_called_bluetooth(self):
        self.assertEqual(detect([interface(0x9999)])[0]['connection'], 'unknown')

    def test_bluetooth_path_works_with_older_hidapi(self):
        bt = interface(0x0270, bus=0)
        bt['path'] = b'\\\\?\\HID#BTHLEDevice#test'
        self.assertEqual(detect([bt])[0]['connection'], 'bluetooth')

    def test_forced_touchpad_pid_is_rejected_before_open(self):
        class Hid:
            enumerate = staticmethod(lambda v, p: [interface(0x3282, 'HIDI2C Device', 3)])
            device = staticmethod(lambda: (_ for _ in ()).throw(AssertionError('must not open')))
        with patch.object(device, 'hid', Hid):
            self.assertFalse(device.SM809Pro(pid=0x3282).open())

    def test_controller_switches_between_receiver_and_cable(self):
        from app.controller import DeviceController
        for source, target in [(0x809f, 0x809e), (0x809e, 0x809f)]:
            ctrl = DeviceController()
            ctrl._dev.pid = source
            ctrl._dev.connection = 'wired' if source == 0x809e else '2.4GHz'
            ctrl._last_keepalive = time.time()
            modes = detect([interface(target)])
            with patch('app.controller.detect_modes', return_value=modes), patch.object(ctrl, '_teardown_device') as teardown:
                ctrl._maintain_connection()
                teardown.assert_called_once()


if __name__ == '__main__':
    unittest.main()
