# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Single-File Portable Specification for RSMF Analyzer
Packages entire application into a single standalone portable executable (RSMFInspector_Portable.exe).
Strictly targets PySide6 6.7.3 for Windows Server 2016 (Build 14393) & Windows 10/11.
"""

import os
import sys

block_cipher = None

# Project root directory
project_root = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'assets'), 'assets'),
    ],
    hiddenimports=[
        'rsmf_inspector',
        'rsmf_inspector.models.rsmf_payload',
        'rsmf_inspector.services.rsmf_parser',
        'rsmf_inspector.services.async_workers',
        'rsmf_inspector.services.temp_cache_service',
        'rsmf_inspector.services.rsmf_export_service',
        'rsmf_inspector.ui.main_window',
        'rsmf_inspector.ui.file_list_pane',
        'rsmf_inspector.ui.attachment_pane',
        'rsmf_inspector.ui.metric_cards',
        'rsmf_inspector.ui.tabbed_viewer',
        'rsmf_inspector.ui.rsmf_chat_tab',
        'rsmf_inspector.ui.json_view_tab',
        'rsmf_inspector.ui.json_highlighter',
        'rsmf_inspector.ui.participants_dialog',
        'PIL',
        'pillow_heif',
        'cv2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(project_root, 'rsmf_inspector', 'win_compat_hook.py')],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RSMFInspector_Portable',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'assets', 'app_icon.ico'),
)

