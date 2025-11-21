"""Docker Sandbox Executor for safe code execution."""

import docker
import tempfile
import os
import time
import structlog
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import tarfile
import io

from app.config import settings

logger = structlog.get_logger()


class DockerSandboxExecutor:
    """
    Executes code in isolated Docker containers with security constraints.
    """
    
    def __init__(self):
        """Initialize Docker client and configuration."""
        self.client = docker.from_env()
        self.timeout = settings.DOCKER_TIMEOUT
        self.max_memory = settings.DOCKER_MAX_MEMORY
        self.max_cpu = settings.DOCKER_MAX_CPU
        
    def execute_code(
        self,
        code: str,
        language: str = "python",
        test_command: Optional[str] = None,
        dependencies: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str, str]:
        """
        Execute code in a sandboxed Docker container.
        
        Args:
            code: The code to execute
            language: Programming language (python, javascript, etc.)
            test_command: Optional test command to run
            dependencies: Dict of dependency files (e.g., requirements.txt)
            files: Additional files to include in the container
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        container = None
        
        try:
            # Select base image based on language
            base_image = self._get_base_image(language)
            
            logger.info(f"Creating sandbox container with image: {base_image}")
            
            # Create temporary directory for code
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
                
                # Create container with security constraints
                container = self.client.containers.create(
                    image=base_image,
                    command="/bin/sh",
                    stdin_open=True,
                    tty=False,
                    mem_limit=self.max_memory,
                    cpu_quota=int(self.max_cpu * 100000),
                    cpu_period=100000,
                    network_mode="none",  # No network access
                    read_only=False,  # Allow writes to /tmp
                    working_dir="/workspace",
                    environment={
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "PYTHONUNBUFFERED": "1"
                    },
                    volumes={
                        tmpdir: {
                            "bind": "/workspace",
                            "mode": "rw"
                        }
                    }
                )
                
                # Start container
                container.start()
                
                # Install dependencies if needed
                if dependencies and "requirements.txt" in dependencies:
                    install_result = container.exec_run(
                        "pip install -r requirements.txt",
                        workdir="/workspace"
                    )
                    if install_result.exit_code != 0:
                        logger.warning(f"Failed to install dependencies: {install_result.output.decode()}")
                
                # Execute the code or test command
                if test_command:
                    exec_command = test_command
                else:
                    exec_command = self._get_exec_command(language, code_file)
                
                logger.info(f"Executing command: {exec_command}")
                
                # Run with timeout
                start_time = time.time()
                exec_result = container.exec_run(
                    exec_command,
                    workdir="/workspace",
                    demux=True
                )
                
                execution_time = time.time() - start_time
                
                # Parse results
                stdout = exec_result.output[0].decode() if exec_result.output[0] else ""
                stderr = exec_result.output[1].decode() if exec_result.output[1] else ""
                success = exec_result.exit_code == 0
                
                logger.info(
                    "Code execution completed",
                    success=success,
                    execution_time=execution_time,
                    exit_code=exec_result.exit_code
                )
                
                return success, stdout, stderr
                
        except Exception as e:
            logger.error(f"Sandbox execution failed: {str(e)}")
            return False, "", str(e)
            
        finally:
            # Clean up container
            if container:
                try:
                    container.stop(timeout=5)
                    container.remove(force=True)
                    logger.info("Sandbox container cleaned up")
                except Exception as e:
                    logger.error(f"Failed to clean up container: {str(e)}")
    
    def _get_base_image(self, language: str) -> str:
        """Get Docker base image for the language."""
        images = {
            "python": "python:3.9-slim",
            "javascript": "node:18-slim",
            "typescript": "node:18-slim",
            "java": "openjdk:11-slim",
            "go": "golang:1.21-alpine",
            "rust": "rust:slim",
            "ruby": "ruby:3.1-slim",
            "php": "php:8.1-cli"
        }
        return images.get(language, "python:3.9-slim")
    
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
            "python": f"python {filename}",
            "javascript": f"node {filename}",
            "typescript": f"npx ts-node {filename}",
            "java": f"javac {filename} && java Main",
            "go": f"go run {filename}",
            "rust": f"rustc {filename} && ./main",
            "ruby": f"ruby {filename}",
            "php": f"php {filename}"
        }
        return commands.get(language, f"python {filename}")
    
    def validate_container_resources(self) -> bool:
        """Validate Docker daemon is accessible and has resources."""
        try:
            info = self.client.info()
            logger.info(
                "Docker daemon accessible",
                containers_running=info.get("ContainersRunning", 0),
                images=info.get("Images", 0)
            )
            return True
        except Exception as e:
            logger.error(f"Docker daemon not accessible: {str(e)}")
            return False
