"""Packet regression tests: no HID connection or device writes."""
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from sm809pro import SM809Pro, actions as A, protocol as P
from sm809pro import device as device_module
from tools.inspect_key_report import inspect_report


class WheelMappingTests(unittest.TestCase):
    def capture(self, codes):
        dev = SM809Pro()
        packets = []
        dev._send_packet = lambda packet: packets.append(bytes(packet)) or True
        self.assertTrue(dev.set_keys(codes))
        self.assertEqual(len(packets), 2)
        self.assertEqual([p[2] for p in packets], [0x02, 0x12])
        for packet in packets:
            self.assertEqual(len(packet), 31)
            self.assertEqual(packet[3], (6 + sum(packet[:3]) + sum(packet[4:])) & 255)
        slots = [tuple(p[4+i*3:7+i*3]) for p in packets for i in range(9)]
        return packets, slots

    def test_factory_wheel_bytes_match_official_restored_profile(self):
        packets, slots = self.capture(A.default_button_codes())
        self.assertEqual(packets[1][-6:], bytes.fromhex('10 20 00 10 40 00'))
        self.assertEqual(slots[16:], [(0x10, 0x20, 0), (0x10, 0x40, 0)])
        self.assertEqual(A.NUM_BUTTONS, 16)
        self.assertEqual(len(A.physical_to_slots(A.default_button_codes())), 16)

    def test_every_physical_button_remap_keeps_wheel_and_other_buttons(self):
        default = A.default_button_codes()
        for physical in range(16):
            with self.subTest(physical_button=physical+1):
                codes = default.copy()
                codes[physical] = (0x70, 0, 0x04 + physical)
                _, slots = self.capture(codes)
                self.assertEqual(slots[:16], A.physical_to_slots(codes))
                self.assertEqual(tuple(slots[16:]), A.WHEEL_ROTATION_DEFAULTS)

    def test_repeated_profile_maps_and_macro_bindings_preserve_wheel(self):
        dev = SM809Pro()
        packets = []
        dev._send_packet = lambda packet: packets.append(bytes(packet)) or True
        first = A.default_button_codes()
        second = first.copy()
        second[0] = (0x90, 3, 0)  # macro reference stays a physical-button action
        second[7] = A.BTN['disable']
        for codes in (first, second, first):
            self.assertTrue(dev.set_keys(codes))
            slots = [tuple(p[4+i*3:7+i*3]) for p in packets[-2:] for i in range(9)]
            self.assertEqual(slots[:16], A.physical_to_slots(codes))
            self.assertEqual(tuple(slots[16:]), A.WHEEL_ROTATION_DEFAULTS)
        self.assertEqual([p[1] for p in packets], [1, 2, 3, 4, 5, 6])

    def test_failed_write_is_reported(self):
        dev = SM809Pro()
        with patch.object(dev, '_send_packet', side_effect=[True, False]):
            self.assertFalse(dev.set_keys_default())

    def test_decoder_accepts_full_mapping_and_rejects_corrupt_capture(self):
        packets, _ = self.capture(A.default_button_codes())
        report = bytes([6]) + packets[1]
        decoded = inspect_report(report.hex())
        self.assertTrue(decoded['normal_wheel'])
        self.assertEqual(decoded['slots']['16'], '10 20 00')
        corrupt = bytearray(report)
        corrupt[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'Checksum'):
            inspect_report(corrupt.hex())
        with self.assertRaisesRegex(ValueError, '32 report bytes'):
            inspect_report(report[1:].hex())

    def test_cable_809e_is_classified_as_wired(self):
        class FakeHid:
            @staticmethod
            def enumerate(vid, pid):
                if vid == P.VID and pid in (0, 0x809E):
                    return [dict(product_id=0x809E, usage_page=0x0A,
                                 usage=1, path=b'fake#Col05')]
                return []
        with patch.object(device_module, 'hid', FakeHid):
            modes = device_module.detect_modes()
        self.assertEqual(len(modes), 1)
        self.assertEqual(modes[0]['connection'], 'wired')
        self.assertEqual(device_module.choose_mode(modes)['pid'], 0x809E)


if __name__ == '__main__':
    unittest.main(verbosity=2)
