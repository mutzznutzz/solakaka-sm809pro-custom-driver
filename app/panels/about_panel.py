"""Credits and an explicitly refreshed, read-only diagnostic report."""
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit, QScrollArea, QApplication
from ..identity import APP_NAME, APP_VERSION, FORK_URL, UPSTREAM_URL
from ..widgets.controls import Card


class AboutPanel(QWidget):
    refresh_requested = Signal()

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        title = QLabel('About and Diagnostics')
        title.setProperty('panelTitle', 'true')
        outer.addWidget(title)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        holder = QWidget()
        root = QVBoxLayout(holder)
        root.setContentsMargins(0, 10, 0, 0)
        info = Card(APP_NAME.upper(), 'Version ' + APP_VERSION)
        self.credits = QLabel(
            'Based on the SM809 Pro custom-driver project by lacno29.\n\n'
            'Enhancements, feature direction and hardware testing by\n'
            'Robin Luxton at MutzNutz Media and Design.\n\n'
            'Wheel mapping fixes, corrected DPI stage handling, improved connection '
            'detection, interface enhancements, backups and profile-setting undo.\n\n'
            'Development process: AI-assisted development.')
        self.credits.setWordWrap(True)
        self.credits.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info.add(self.credits)
        links = QLabel(f'<a style="color:#36C5F0" href="{UPSTREAM_URL}">Original project</a> &nbsp; | &nbsp; <a style="color:#36C5F0" href="{FORK_URL}">Improved fork</a>')
        links.setOpenExternalLinks(True)
        info.add(links)
        licence = QLabel('Upstream licence: not specified in the original repository. Redistribution permission has not been confirmed. SOLAKAKA is the hardware brand; this is an independent project. Built with PySide6/Qt and hidapi, under their respective licence terms.')
        licence.setWordWrap(True)
        licence.setProperty('cardHint', 'true')
        info.add(licence)
        root.addWidget(info)
        diagnostics = Card('DIAGNOSTICS', 'Read-only device information and recent errors. No key assignments, macros, serial numbers or raw device paths are included.')
        self.report = QPlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setMinimumHeight(190)
        diagnostics.add(self.report)
        buttons = QHBoxLayout()
        refresh = QPushButton('Refresh diagnostics')
        refresh.clicked.connect(self.refresh_requested)
        copy = QPushButton('Copy report')
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.report.toPlainText()))
        buttons.addWidget(refresh)
        buttons.addWidget(copy)
        buttons.addStretch(1)
        diagnostics.add(buttons)
        root.addWidget(diagnostics)
        root.addStretch(1)
        scroll.setWidget(holder)
        outer.addWidget(scroll, 1)

    def set_report(self, text):
        self.report.setPlainText(text)
