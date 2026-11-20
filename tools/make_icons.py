"""Render original application/tray artwork into Windows multi-size icons."""
import os
import pathlib
import struct
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter, QRadialGradient, QColor
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtSvg import QSvgRenderer

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'images'
SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
<defs><radialGradient id="halo" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#29d9eb" stop-opacity="0.5"/><stop offset="65%" stop-color="#29d9eb" stop-opacity="0.18"/><stop offset="100%" stop-color="#29d9eb" stop-opacity="0"/></radialGradient>
<linearGradient id="body" x2="0" y2="1"><stop stop-color="#273440"/><stop offset="1" stop-color="#101820"/></linearGradient></defs>
{back}<rect x="67" y="35" width="122" height="186" rx="59" fill="url(#body)" stroke="#eafaff" stroke-width="12"/>
<path d="M128 40v48" stroke="#eafaff" stroke-width="10"/>
<rect x="115" y="68" width="26" height="44" rx="13" fill="#ff7134"/>
<path d="M104 159l24-22 24 22m-48 22 24-22 24 22" fill="none" stroke="#29d9eb" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

TRAY_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
<defs><radialGradient id="halo"><stop offset="0%" stop-color="#29d9eb" stop-opacity="0.5"/><stop offset="100%" stop-color="#29d9eb" stop-opacity="0"/></radialGradient></defs>
{back}<rect x="30" y="10" width="196" height="236" rx="88" fill="#182735" stroke="#eafaff" stroke-width="14"/>
<path d="M128 18v94M39 112h178" stroke="#36c5f0" stroke-width="9"/>
<rect x="112" y="42" width="32" height="54" rx="15" fill="#ff7134"/>
</svg>'''

def make(name, tray=False):
    back = '<circle cx="128" cy="128" r="128" fill="url(#halo)"/>' if tray else '<rect x="5" y="5" width="246" height="246" rx="54" fill="#0e1720"/>'
    artwork = TRAY_SVG if tray else SVG
    svg = artwork.replace('{back}', back)
    (ROOT / (name + '.svg')).write_text(svg, encoding='utf-8')
    renderer = QSvgRenderer(artwork.replace('{back}', '' if tray else back).encode())
    entries, payloads = [], []
    sizes = (16, 20, 24, 32, 48, 64, 128, 256)
    offset = 6 + 16 * len(sizes)
    for size in sizes:
        img = QImage(size, size, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        painter = QPainter(img)
        if tray:
            painter.setRenderHint(QPainter.Antialiasing)
            gradient = QRadialGradient(size / 2, size / 2, size / 2)
            gradient.setColorAt(0, QColor(41, 217, 235, 130))
            gradient.setColorAt(0.65, QColor(41, 217, 235, 65))
            gradient.setColorAt(1, QColor(41, 217, 235, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(gradient)
            painter.drawEllipse(0, 0, size, size)
        renderer.render(painter)
        painter.end()
        data = QByteArray()
        buf = QBuffer(data)
        buf.open(QIODevice.WriteOnly)
        img.save(buf, 'PNG')
        payload = bytes(data)
        entries.append(struct.pack('<BBBBHHII', size % 256, size % 256, 0, 0, 1, 32, len(payload), offset))
        payloads.append(payload)
        offset += len(payload)
        if size == 256:
            img.save(str(ROOT / (name + '-preview.png')))
    (ROOT / (name + '.ico')).write_bytes(struct.pack('<HHH', 0, 1, len(sizes)) + b''.join(entries + payloads))

if __name__ == '__main__':
    app = QApplication([])
    make('icon')
    make('tray-icon', True)
