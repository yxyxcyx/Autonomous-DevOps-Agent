"""Simple executor fallback when Docker is not available."""

import subprocess
import tempfile
import os
import structlog
from typing import Tuple, Optional, Dict, List
import sys
import shlex

logger = structlog.get_logger()


class SimpleExecutor:
    """
    Simple code executor as fallback when Docker is not available.
    WARNING: This runs code directly on the host - use only for testing!
    """
    
    def execute_code(
        self,
        code: str,
        language: str = "python",
        test_command: Optional[str] = None,
        dependencies: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> Tuple[bool, str, str]:
        """
        Execute code in a simple subprocess (no sandboxing).
        
        WARNING: This is NOT secure and should only be used for testing!
        """
        logger.warning("Using simple executor without sandboxing - NOT SECURE!")
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write code file
                code_file = self._get_code_filename(language)
                code_path = os.path.join(tmpdir, code_file)
                
                with open(code_path, 'w') as f:
                    f.write(code)
                
                # Write additional files
                if files:
                    for filename, content in files.items():
                        file_path = os.path.join(tmpdir, filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, 'w') as f:
                            f.write(content)
                
                # Write dependencies
                if dependencies:
                    for dep_file, content in dependencies.items():
                        dep_path = os.path.join(tmpdir, dep_file)
                        with open(dep_path, 'w') as f:
                            f.write(content)
                
                # Determine command to run
                if test_command:
                    cmd = self._split_command(test_command)
                else:
                    cmd = self._split_command(self._get_exec_command(language, code_file))
                
                # Run the command
                logger.info(f"Executing command: {cmd}")
                
                result = subprocess.run(
                    cmd,
                    shell=False,
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                success = result.returncode == 0
                stdout = result.stdout
                stderr = result.stderr
                
                logger.info(f"Execution completed: success={success}")
                
                return success, stdout, stderr
                
        except subprocess.TimeoutExpired:
            return False, "", "Execution timeout exceeded"
        except Exception as e:
            logger.error(f"Simple execution failed: {str(e)}")
            return False, "", str(e)
    
    def _get_code_filename(self, language: str) -> str:
        """Get appropriate filename for the language."""
        extensions = {
            "python": "main.py",
            "javascript": "main.js",
            "typescript": "main.ts",
            "java": "Main.java",
            "go": "main.go",
            "rust": "main.rs",
            "ruby": "main.rb",
            "php": "main.php"
        }
        return extensions.get(language, "main.py")
    
    def _get_exec_command(self, language: str, filename: str) -> str:
        """Get execution command for the language."""
        commands = {
            "python": f"{sys.executable} {filename}",
            "javascript": f"node {filename}",
            "typescript": f"npx ts-node {filename}",
            "java": f"javac {filename} && java Main",
            "go": f"go run {filename}",
            "rust": f"rustc {filename} && ./main",
            "ruby": f"ruby {filename}",
            "php": f"php {filename}"
        }
        return commands.get(language, f"{sys.executable} {filename}")
