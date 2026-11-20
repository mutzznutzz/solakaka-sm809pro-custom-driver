"""
app.panels.lighting_panel -- the side-button lighting configuration panel.

Preset effects plus an experimental RGB picker. The original author's firmware
ignored RGB for solid modes. The picker uses the existing RGB fields, without
assuming another firmware supports them or introducing undocumented commands.

Brightness/speed/direction are likewise NOT exposed -- on this firmware they have
no observable effect (see LIGHTING_NOTE.md). Changes auto-apply to the mouse.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame, QSizePolicy, QPushButton,
)

from .. import theme
from ..widgets.controls import Card
from sm809pro import protocol as P
from sm809pro import defaults as _D
from ..widgets.color_picker import pick_color


def _hline():
    f = QFrame()
    f.setProperty("sep", "true")
    f.setFrameShape(QFrame.NoFrame)
    return f


class LightingPanel(QWidget):
    """Side-button lighting: a single mode selector (auto-applies)."""
    # (mode:int, color:(r,g,b)) -- color is kept for the device call but the
    # single-color modes use predefined colors on this firmware.
    apply_requested = Signal(int, tuple)

    def __init__(self, mode=None, color=None):
        super().__init__()
        self._suspend = False
        self.is_custom = False
        self._mode = _D.LIGHTING_MODE if mode is None else mode
        self._color = tuple(color) if color else tuple(_D.LIGHTING_COLOR)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        title = QLabel("Lighting")
        title.setProperty("panelTitle", "true")
        root.addWidget(title)
        sub = QLabel("Side-button lighting effect.")
        sub.setProperty("panelSubtitle", "true")
        root.addWidget(sub)
        root.addWidget(_hline())

        # --- Effect card: mode dropdown ---
        card = Card("SIDE BUTTON LIGHTING")
        mode_col = QVBoxLayout()
        mode_col.setSpacing(6)
        mlabel = QLabel("Effect")
        mlabel.setProperty("cardHint", "true")
        mode_col.addWidget(mlabel)
        self.mode_combo = QComboBox()
        for m in sorted(P.LIGHTING_MODES):
            self.mode_combo.addItem(P.LIGHTING_MODES[m], m)
        self.mode_combo.addItem("Custom colour (experimental)", 100)
        self.mode_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_col.addWidget(self.mode_combo)
        self.color_button = QPushButton("Choose custom colour")
        self.color_button.clicked.connect(self._choose_color)
        mode_col.addWidget(self.color_button)
        self.custom_note = QLabel("Custom RGB depends on mouse firmware. Some versions use a preset colour instead.")
        self.custom_note.setWordWrap(True)
        self.custom_note.setProperty("cardHint", "true")
        mode_col.addWidget(self.custom_note)
        card.add(mode_col)
        root.addWidget(card)
        root.addStretch(1)

        self._load(self._mode)

    # -- helpers --------------------------------------------------------------
    def _load(self, mode):
        self._suspend = True
        try:
            idx = self.mode_combo.findData(100 if self.is_custom else mode)
            if idx >= 0:
                self.mode_combo.setCurrentIndex(idx)
            self._mode = mode
        finally:
            self._suspend = False

    # -- events ---------------------------------------------------------------
    def _on_mode_changed(self, _idx):
        if self._suspend:
            return
        if self.mode_combo.currentData() == 100:
            self._choose_color()
            return
        self.is_custom = False
        self._mode = self.mode_combo.currentData()
        self.apply_requested.emit(self._mode, self._color)

    def _choose_color(self):
        color = pick_color(self._color, self.window())
        if color is None:
            self._load(self._mode)
            return
        self._color = tuple(color)
        self.is_custom = True
        self._load(8)
        self.color_button.setText("Custom colour: #{:02X}{:02X}{:02X}".format(*color))
        self.apply_requested.emit(8, self._color)

    # -- external -------------------------------------------------------------
    def set_state(self, mode, color=None, custom=False):
        """Load mode from outside (e.g. factory restore) without applying."""
        if color:
            self._color = tuple(color)
        self.is_custom = custom
        self.color_button.setText("Custom colour: #{:02X}{:02X}{:02X}".format(*self._color) if custom else "Choose custom colour")
        self._load(mode)
