"""Supported side-button effects, embedded in Performance and Lighting."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox
from ..widgets.controls import Card
from sm809pro import protocol as P, defaults as D


class LightingPanel(QWidget):
    apply_requested = Signal(int, tuple)

    def __init__(self, mode=None, color=None):
        super().__init__()
        self._suspend = False
        self.is_custom = False  # compatibility with v3 profiles; custom RGB removed
        self._color = tuple(color or D.LIGHTING_COLOR)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        card = Card("SIDE BUTTON LIGHTING", "Choose an effect. Solid colours are limited to red, green and blue.")
        self.mode_combo = QComboBox()
        for mode_id, label in sorted(P.LIGHTING_MODES.items()):
            self.mode_combo.addItem(label, mode_id)
        self.mode_combo.setToolTip("Change the side-button lighting effect. This mouse supports preset colours, not custom RGB.")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        card.add(self.mode_combo)
        root.addWidget(card)
        self.set_state(D.LIGHTING_MODE if mode is None else mode, color)

    def _on_mode_changed(self, _index):
        if not self._suspend:
            self.apply_requested.emit(self.mode_combo.currentData(), self._color)

    def set_state(self, mode, color=None, custom=False):
        """Old custom profiles load as their underlying preset, without writing."""
        self._suspend = True
        try:
            self._color = tuple(color or D.LIGHTING_COLOR)
            self.mode_combo.setCurrentIndex(max(0, self.mode_combo.findData(mode)))
        finally:
            self._suspend = False
