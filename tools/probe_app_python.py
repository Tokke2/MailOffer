"""Offline smoke test in a disposable child process, using shared Python only."""
import importlib
import os
import sys

if sys.prefix != sys.base_prefix:
    raise SystemExit('Separat Python-miljo accepteras inte.')

# Avoid windows and test loading the Qt platform without opening the real app.
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
for name in ('docx', 'darkdetect', 'email_validator', 'deep_translator',
             'PIL.Image', 'bs4', 'qrcode'):
    importlib.import_module(name)
from PyQt6.QtWidgets import QApplication, QWidget
app = QApplication([])
window = QWidget()
app.processEvents()
window.close()
print('App dependencies and Qt OK')
