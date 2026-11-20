"""
app.panels.buttons_panel -- the button remapping panel.

Layout: two columns of compact button rows (left = side macro pad 1-9, right =
buttons 10-16) with a mouse reference image showing the physical numbering.
Each row is clickable and opens the action picker (mirrors the official menu).

Changes auto-apply to the mouse on each button pick; emits the full 16-button
code list, which the main window/controller push to the device.
"""

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QMessageBox, QSpinBox, QCheckBox,
)

from .. import theme
from ..widgets.action_picker import describe_action, pick_action
from sm809pro import actions as A

# mouse reference image (numbered) -- bundled resource (works frozen via _MEIPASS)
from ..paths import resource_path
_IMG = resource_path("images", "mouse.png")

# column split + group labels by physical region (product-image numbering)
LEFT_COLUMN = [1, 2, 3, 4, 5, 6, 7, 8, 9]   # side macro pad
RIGHT_GROUPS = {
    "Thumb Pair": [10, 11],
    "Primary": [12, 13, 14],
    "Top Pair": [15, 16],
}


def _hline():
    f = QFrame()
    f.setProperty("sep", "true")
    f.setFrameShape(QFrame.NoFrame)
    return f


def _group_label(text):
    gl = QLabel(text.upper())
    gl.setProperty("groupLabel", "true")
    return gl


class ButtonRow(QFrame):
    """One physical button: number badge + current-action button (compact)."""
    changed = Signal(int)

    def __init__(self, phys: int, code, get_macros=None):
        super().__init__()
        self.phys = phys
        self._code = code
        self._get_macros = get_macros or (lambda: [])
        self.setObjectName("btnRow")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 7, 10, 7)
        lay.setSpacing(10)

        badge = QLabel(f"{phys}")
        badge.setObjectName("btnBadge")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedSize(24, 24)
        lay.addWidget(badge)

        self.action_btn = QPushButton(describe_action(self._code))
        self.action_btn.setToolTip("Choose what this physical mouse button does in the current profile. Changes apply automatically.")
        self.action_btn.setObjectName("actionField")
        self.action_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.action_btn.clicked.connect(self._open_picker)
        lay.addWidget(self.action_btn, 1)

    def _open_picker(self):
        result = pick_action(self._code, self.window(), phys=self.phys,
                             macros=self._get_macros())
        if result is not None:
            self.set_code(result)
            self.changed.emit(self.phys)

    def set_code(self, code):
        self._code = code if isinstance(code, dict) else tuple(code)
        self.action_btn.setText(describe_action(self._code))

    def refresh_label(self):
        self.action_btn.setText(describe_action(self._code))

    def code(self):
        return self._code


class MouseReference(QFrame):
    """The numbered mouse image, shown for physical-button reference."""
    def __init__(self):
        super().__init__()
        self.setObjectName("mouseRef")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)
        cap = QLabel("REFERENCE")
        cap.setProperty("groupLabel", "true")
        cap.setAlignment(Qt.AlignHCenter)
        lay.addWidget(cap)
        img = QLabel()
        img.setAlignment(Qt.AlignCenter)
        if os.path.exists(_IMG):
            pm = QPixmap(_IMG)
            if not pm.isNull():
                img.setPixmap(pm.scaledToWidth(260, Qt.SmoothTransformation))
        else:
            img.setText("(mouse.png not found)")
            img.setProperty("panelSubtitle", "true")
        lay.addWidget(img)
        lay.addStretch(1)


class ButtonsPanel(QWidget):
    """16-button remap panel: two columns of rows + a mouse reference image."""
    apply_requested = Signal(object)
    wheel_requested = Signal(object)
    reset_requested = Signal()

    def __init__(self, codes=None, get_macros=None):
        super().__init__()
        codes = codes or A.default_button_codes()
        self._get_macros = get_macros or (lambda: [])

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel("Button Assignment")
        title.setProperty("panelTitle", "true")
        root.addWidget(title)
        sub = QLabel("Click any button to assign an action. Numbers match the "
                     "reference image. Changes apply to the mouse automatically.")
        sub.setProperty("panelSubtitle", "true")
        root.addWidget(sub)
        root.addWidget(_hline())

        # scrollable body: [ left col | right col | reference image ]
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        holder = QWidget()
        cols = QHBoxLayout(holder)
        cols.setContentsMargins(0, 0, 0, 0)
        cols.setSpacing(20)

        self.rows = {}

        # left column: side macro pad (1-9)
        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(_group_label("Side Macro Pad"))
        for phys in LEFT_COLUMN:
            row = ButtonRow(phys, codes[phys - 1], get_macros=self._get_macros)
            row.changed.connect(self._on_button_changed)
            self.rows[phys] = row
            left.addWidget(row)
        left.addStretch(1)
        left_w = QWidget(); left_w.setLayout(left)
        cols.addWidget(left_w, 1)

        # right column: the other groups (10-16)
        right = QVBoxLayout()
        right.setSpacing(8)
        for group_name, phys_list in RIGHT_GROUPS.items():
            right.addWidget(_group_label(group_name))
            for phys in phys_list:
                row = ButtonRow(phys, codes[phys - 1], get_macros=self._get_macros)
                row.changed.connect(self._on_button_changed)
                self.rows[phys] = row
                right.addWidget(row)
        right.addWidget(_group_label("Wheel Rotation"))
        self._wheel = list(A.WHEEL_ROTATION_DEFAULTS)
        self.wheel_buttons = []
        for i, name in enumerate(("Scroll Up", "Scroll Down")):
            button = QPushButton()
            button.setToolTip("Choose the action sent for this wheel direction. This does not change middle-click.")
            button.clicked.connect(lambda checked=False, index=i: self._edit_wheel(index))
            self.wheel_buttons.append(button)
            right.addWidget(QLabel(name))
            right.addWidget(button)
        normal = QPushButton("Restore normal scrolling")
        normal.setToolTip("Restore wheel-up and wheel-down actions only. Other button assignments and the Windows scroll amount stay unchanged.")
        normal.clicked.connect(self._reset_wheel)
        right.addWidget(normal)
        self.set_wheel(A.WHEEL_ROTATION_DEFAULTS)
        hint = QLabel("Wheel rotation is separate from middle-click (14).")
        hint.setWordWrap(True)
        hint.setProperty("panelSubtitle", "true")
        right.addWidget(hint)
        lines = QHBoxLayout()
        self.scroll_lines = QSpinBox()
        self.scroll_lines.setRange(1, 100)
        self.scroll_lines.setToolTip("Windows-wide number of lines per wheel step, used by apps that follow the Windows scroll setting. Click Apply to save.")
        self.scroll_lines.setValue(3)
        self.scroll_page = QCheckBox("One page")
        self.scroll_page.setToolTip("Request one page per wheel step instead of a line count. Click Apply to save this for Windows.")
        try:
            import ctypes
            value = ctypes.c_uint()
            if ctypes.windll.user32.SystemParametersInfoW(0x68, 0, ctypes.byref(value), 0):
                self.scroll_page.setChecked(value.value == 0xffffffff)
                if value.value != 0xffffffff:
                    self.scroll_lines.setValue(value.value)
        except (AttributeError, OSError):
            pass
        lines.addWidget(QLabel("Lines"))
        lines.addWidget(self.scroll_lines)
        lines.addWidget(self.scroll_page)
        right.addLayout(lines)
        apply_lines = QPushButton("Apply scroll amount to Windows")
        apply_lines.setToolTip("System-wide setting for all mice. Not stored in mouse profiles.")
        apply_lines.clicked.connect(self._apply_scroll_lines)
        right.addWidget(apply_lines)
        right.addStretch(1)
        right_w = QWidget(); right_w.setLayout(right)
        cols.addWidget(right_w, 1)

        # reference image column
        cols.addWidget(MouseReference(), 0)

        scroll.setWidget(holder)
        root.addWidget(scroll, 1)

    def _on_button_changed(self, _phys):
        # auto-apply: a button pick is discrete, so push immediately
        self._emit_apply()

    def set_wheel(self, codes):
        self._wheel = [tuple(c) for c in codes]
        for button, code in zip(self.wheel_buttons, self._wheel):
            button.setText(describe_action(code))

    def _edit_wheel(self, index):
        result = pick_action(self._wheel[index], self.window(), macros=[])
        if result is None:
            return
        if isinstance(result, dict) or result[0] == 0x90 or tuple(result) == A.BTN['run_app']:
            QMessageBox.information(self, "Wheel action", "Choose a key combination, mouse action or media action. Wheel macros and app launchers aren't supported here yet.")
            return
        self._wheel[index] = tuple(result)
        self.set_wheel(self._wheel)
        self.wheel_requested.emit(self._wheel.copy())

    def _reset_wheel(self):
        self.set_wheel(A.WHEEL_ROTATION_DEFAULTS)
        self.wheel_requested.emit(self._wheel.copy())

    def _apply_scroll_lines(self):
        try:
            import ctypes
            amount = 0xffffffff if self.scroll_page.isChecked() else self.scroll_lines.value()
            if not ctypes.windll.user32.SystemParametersInfoW(0x69, amount, None, 3):
                raise OSError("Windows did not accept the setting")
        except (AttributeError, OSError) as error:
            QMessageBox.warning(self, "Scroll amount", str(error))

    def _emit_apply(self):
        codes = [self.rows[p].code() for p in range(1, A.NUM_BUTTONS + 1)]
        self.apply_requested.emit(codes)

    def set_codes(self, codes):
        for p in range(1, A.NUM_BUTTONS + 1):
            self.rows[p].set_code(codes[p - 1])

    def bindings(self):
        """The current 16-entry list of bindings (tuples and/or macro dicts)."""
        return [self.rows[p].code() for p in range(1, A.NUM_BUTTONS + 1)]

    def set_binding(self, phys, code):
        """Set one button's binding (1-based physical index)."""
        if phys in self.rows:
            self.rows[phys].set_code(code)

    def refresh_labels(self):
        """Re-render every row's label (e.g. after a macro rename/delete)."""
        for p in range(1, A.NUM_BUTTONS + 1):
            self.rows[p].refresh_label()
