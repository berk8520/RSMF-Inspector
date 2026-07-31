import os
import shutil
import subprocess
from typing import Tuple, Dict, Any

DEFAULT_VALIDATOR_PATH = r"C:\code\python\RsmfInspector\reference Code\rsmf-validator-samples-master"

class ValidatorBridge:
    def __init__(self, validator_dir: str = DEFAULT_VALIDATOR_PATH):
        self.validator_dir = validator_dir
        self.dotnet_path = shutil.which("dotnet")

    def is_validator_available(self) -> Tuple[bool, str]:
        """Check if validator source or executable exists."""
        if not os.path.exists(self.validator_dir):
            return False, f"Validator directory not found: {self.validator_dir}"
        
        # Check if dotnet executable is installed
        if not self.dotnet_path:
            return False, "dotnet CLI is not installed or not found in system PATH."

        # Check for .csproj or .sln
        sln_path = os.path.join(self.validator_dir, "RSMFValidatorSampleCode.sln")
        if os.path.exists(sln_path):
            return True, f"Found C# Validator Solution: {sln_path}"

        return False, f"RSMFValidatorSampleCode project files missing in {self.validator_dir}"

    def validate_rsmf(self, file_path: str) -> Dict[str, Any]:
        """
        Executes the C# validator against an RSMF file container.
        Returns result dict with keys: 'is_valid', 'message', 'output_log', 'status_code'.
        """
        available, msg = self.is_validator_available()
        if not available:
            return {
                "is_valid": None,  # Indeterminate / Skipped
                "message": f"Validator Skipped: {msg}",
                "output_log": f"[VALIDATOR NOTICE]\n{msg}\nTo run live C# validation, install the .NET SDK.",
                "status_code": -1
            }

        try:
            # Build dotnet run command
            # The project structure: RSMFValidatorSampleCode/RSMFValidatorSampleCode.csproj
            proj_path = os.path.join(self.validator_dir, "RSMFValidatorSampleCode", "RSMFValidatorSampleCode.csproj")
            if not os.path.exists(proj_path):
                proj_path = self.validator_dir

            cmd = ["dotnet", "run", "--project", proj_path, "--", file_path]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.validator_dir,
                timeout=30
            )

            is_valid = (result.returncode == 0)
            output_log = f"=== C# Validator Output ===\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

            return {
                "is_valid": is_valid,
                "message": "RSMF Compliance Validation Passed!" if is_valid else "RSMF Validation Errors Detected",
                "output_log": output_log,
                "status_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                "is_valid": False,
                "message": "Validator process timed out (30s).",
                "output_log": "[ERROR] Validation process exceeded 30 seconds execution limit.",
                "status_code": -2
            }
        except Exception as ex:
            return {
                "is_valid": False,
                "message": f"Validation invocation error: {str(ex)}",
                "output_log": f"[EXCEPTION]\n{str(ex)}",
                "status_code": -3
            }
