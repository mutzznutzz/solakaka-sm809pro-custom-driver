"""Packaged GUI startup check with HID and user-profile access disabled."""
import argparse
import json
import os
import pathlib
import tempfile
import traceback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--self-test-result', required=True, type=pathlib.Path)
    parser.add_argument('--self-test-native', action='store_true',
                        help='Use Windows Qt platform instead of offscreen')
    args = parser.parse_args()
    result = {'ok': False, 'hardware_access': 'disabled'}
    try:
        if not args.self_test_native:
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        from PySide6.QtWidgets import QApplication
        from . import paths, controller, profile_store, macro_store
        # Fail closed: no controller starts, and even an accidental open fails.
        from sm809pro import device
        device.hid = None
        controller.DeviceController.start = lambda self: None
        with tempfile.TemporaryDirectory(prefix='sm809-startup-test-') as tmp:
            paths.app_dir = lambda: tmp
            profile_store.default_path = lambda: os.path.join(tmp, 'profiles.json')
            macro_store.default_path = lambda: os.path.join(tmp, 'macros.json')
            from .main_window import MainWindow
            app = QApplication([])
            window = MainWindow()
            window.show()
            app.processEvents()
            result.update(ok=True, gui='MainWindow created and rendered',
                          overlay_present=window.overlay is not None)
            window.ctrl.shutdown()
            if getattr(window, 'tray', None):
                window.tray.hide()
            window.hide()
            window.deleteLater()
            app.processEvents()
            app.quit()
    except Exception:
        result['error'] = traceback.format_exc()
    args.self_test_result.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return 0 if result['ok'] else 1
