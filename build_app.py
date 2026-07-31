"""
Automated Build & Packaging Pipeline for RSMF Inspector
Target OS: Windows Server 2016 (Build 14393) & Windows 10/11
Required PySide6 Version: 6.7.3
"""

import sys
import os
import subprocess

def verify_environment():
    print("--- 1. Verifying PySide6 Version ---")
    try:
        import PySide6
        version = PySide6.__version__
        print(f"Detected PySide6 Version: {version}")
        if version != "6.7.3":
            print(f"[WARNING] Installed PySide6 is {version}. Version 6.7.3 is strongly recommended for Windows Server 2016 compatibility.")
        else:
            print("[SUCCESS] PySide6==6.7.3 verified cleanly.")
    except ImportError:
        print("[ERROR] PySide6 is not installed in current Python environment.")
        sys.exit(1)

def run_pyinstaller_build(portable_mode: bool = True):
    print("\n--- 2. Executing PyInstaller Build ---")
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    spec_filename = "RSMFInspector_OneFile.spec" if portable_mode else "RSMFInspector.spec"
    spec_path = os.path.join(project_root, spec_filename)
    
    if not os.path.exists(spec_path):
        print(f"[ERROR] Spec file missing: {spec_path}")
        sys.exit(1)

    cmd = [sys.executable, "-m", "PyInstaller", spec_path, "--clean", "--noconfirm"]
    print(f"Running build for {'PORTABLE SINGLE-FILE EXE' if portable_mode else 'DIRECTORY BUNDLE'}:")
    print(f"  Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=project_root)
    if result.returncode == 0:
        if portable_mode:
            dist_exe = os.path.join(project_root, "dist", "RSMFInspector_Portable.exe")
        else:
            dist_exe = os.path.join(project_root, "dist", "RSMFInspector", "RSMFInspector.exe")
            
        print("\n========================================================")
        print("BUILD SUCCESSFUL!")
        print(f"Portable Output Executable: {dist_exe}")
        print("Target Environment: Windows Server 2016 & Windows 10/11")
        print("========================================================")
    else:
        print(f"\n[ERROR] PyInstaller build failed with exit code {result.returncode}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    verify_environment()
    run_pyinstaller_build(portable_mode=True)
