# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('arrowflow.ico', '.')]
binaries = []
hiddenimports = [
    'auth',
    'auth.auth_service',
    'auth.firebase_client',
    'auth.totp_manager',
    'pyotp',
    'qrcode',
    'PIL',
    'PIL.ImageTk',
    'PIL.Image',
    'requests',
    'updater',
    'updater.client',
    'updater.manifest',
    'updater.verifier'
]
tmp_ret = collect_all('pynput')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_qr = collect_all('qrcode')
datas += tmp_qr[0]; binaries += tmp_qr[1]; hiddenimports += tmp_qr[2]

# ─────────────────────────────────────────────────────────────────────────────
# 1. Main Application Executable (ArrowFlow.exe)
# ─────────────────────────────────────────────────────────────────────────────
a1 = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz1 = PYZ(a1.pure)
exe1 = EXE(
    pyz1,
    a1.scripts,
    a1.binaries,
    a1.datas,
    [],
    name='ArrowFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['arrowflow.ico'],
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Standalone Updater & Bootstrapper Executable (ArrowFlowUpdater.exe)
# ─────────────────────────────────────────────────────────────────────────────
a2 = Analysis(
    ['updater_app.py'],
    pathex=[],
    binaries=[],
    datas=[('arrowflow.ico', '.')],
    hiddenimports=['updater', 'updater.verifier', 'updater.manifest'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz2 = PYZ(a2.pure)
exe2 = EXE(
    pyz2,
    a2.scripts,
    a2.binaries,
    a2.datas,
    [],
    name='ArrowFlowUpdater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['arrowflow.ico'],
)
