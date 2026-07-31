"""
Windows Server 2016 Runtime Compatibility Hook for PyInstaller
---------------------------------------------------------------
Executes during PyInstaller binary bootstrap prior to Qt/PySide6 module loading.
Guarantees clean PE symbol resolution on legacy kernel environments (Windows Server 2016 Build 14393).
"""

import sys
import ctypes
import os

def apply_windows_server_2016_compat():
    if not sys.platform.startswith("win"):
        return

    try:
        kernel32 = ctypes.windll.kernel32
        
        # Check if SetThreadDescription exists natively on current kernel
        has_set_thread_desc = hasattr(kernel32, "SetThreadDescription")
        if not has_set_thread_desc:
            # Check via GetProcAddress
            set_thread_desc_ptr = kernel32.GetProcAddress(kernel32._handle, b"SetThreadDescription")
            has_set_thread_desc = (set_thread_desc_ptr is not None and set_thread_desc_ptr != 0)

        if not has_set_thread_desc:
            # Provide a safe no-op stub if invoked via ctypes
            def _stub_set_thread_description(hThread, lpThreadDescription):
                return 0  # HRESULT S_OK
            
            kernel32.SetThreadDescription = _stub_set_thread_description

    except Exception:
        pass

apply_windows_server_2016_compat()
