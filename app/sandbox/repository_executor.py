"""Repository-aware sandbox executor that tests against actual code."""

import os
import tempfile
import shutil
import docker
import time
from typing import Tuple, Optional, Dict, Any
import structlog
from app.config import settings

logger = structlog.get_logger()


class RepositoryExecutor:
    """
    Executes code patches against actual repository code in Docker.
    """
    
    def __init__(
        self,
        timeout: int = None,
        max_memory: str = None,
        max_cpu: float = None
    ):
        """
        Initialize the repository executor.
        
        Args:
            timeout: Maximum execution time in seconds
            max_memory: Maximum memory limit (e.g., "512m")
            max_cpu: Maximum CPU usage (0.5 = 50% of one core)
        """
        self.timeout = timeout or settings.DOCKER_TIMEOUT
        self.max_memory = max_memory or settings.DOCKER_MAX_MEMORY
        self.max_cpu = max_cpu or settings.DOCKER_MAX_CPU
        self.client = docker.from_env()
    
    def execute_with_repository(
        self,
        repo_path: str,
        patch_data: Dict[str, str],
        test_command: str,
        language: str = "python"
    ) -> Tuple[bool, str, str]:
        """
        Execute tests with patched repository code.
        
        Args:
            repo_path: Path to cloned repository
            patch_data: Dictionary of file paths to patched content
            test_command: Command to run tests
            language: Programming language
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        container = None
        
        try:
            # Create temporary copy of repository
            with tempfile.TemporaryDirectory() as tmpdir:
                # Copy entire repository
                repo_copy = os.path.join(tmpdir, "repo")
                shutil.copytree(repo_path, repo_copy, ignore=shutil.ignore_patterns('.git'))
                
                # Apply patches
                for file_path, content in patch_data.items():
                    full_path = os.path.join(repo_copy, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, 'w') as f:
                        f.write(content)
                    logger.info(f"Applied patch to {file_path}")
                
                # Get base image
                base_image = self._get_base_image(language)
                
                # Create container with repository code
                container = self.client.containers.create(
                    image=base_image,
                    command="/bin/sh",
                    stdin_open=True,
                    tty=False,
                    mem_limit=self.max_memory,
                    cpu_quota=int(self.max_cpu * 100000),
                    cpu_period=100000,
                    network_mode="bridge",  # Allow network for package installation
                    working_dir="/workspace",
                    environment={
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "PYTHONUNBUFFERED": "1",
                        "CI": "true"  # Set CI environment variable
                    },
                    volumes={
                        repo_copy: {
                            "bind": "/workspace",
                            "mode": "rw"
                        }
                    }
                )
                
                # Start container
                container.start()
                
                # Install dependencies if requirements file exists
                dependency_files = {
                    "python": ["requirements.txt", "setup.py", "pyproject.toml"],
                    "javascript": ["package.json"],
                    "typescript": ["package.json"],
                    "java": ["pom.xml", "build.gradle"],
                    "go": ["go.mod"],
                    "rust": ["Cargo.toml"],
                    "ruby": ["Gemfile"],
                    "php": ["composer.json"]
                }
                
                if language in dependency_files:
                    for dep_file in dependency_files[language]:
                        dep_path = os.path.join(repo_copy, dep_file)
                        if os.path.exists(dep_path):
                            install_cmd = self._get_install_command(language, dep_file)
                            if install_cmd:
                                logger.info(f"Installing dependencies: {install_cmd}")
                                install_result = container.exec_run(
                                    install_cmd,
                                    workdir="/workspace",
                                    demux=True
                                )
                                if install_result.exit_code != 0:
                                    stderr = install_result.output[1].decode() if install_result.output[1] else ""
                                    logger.warning(f"Dependency installation warning: {stderr}")
                            break
                
                # Run the actual test command
                logger.info(f"Running test command: {test_command}")
                
                start_time = time.time()
                exec_result = container.exec_run(
                    test_command,
                    workdir="/workspace",
                    demux=True,
                    environment={
                        "PYTHONPATH": "/workspace",
                        "PATH": "/usr/local/bin:/usr/bin:/bin"
                    }
                )
                
                execution_time = time.time() - start_time
                
                # Parse results
                stdout = exec_result.output[0].decode() if exec_result.output[0] else ""
                stderr = exec_result.output[1].decode() if exec_result.output[1] else ""
                success = exec_result.exit_code == 0
                
                logger.info(
                    "Repository test execution completed",
                    success=success,
                    execution_time=execution_time,
                    exit_code=exec_result.exit_code
                )
                
                return success, stdout, stderr
                
        except Exception as e:
            logger.error(f"Repository execution failed: {str(e)}")
            return False, "", str(e)
            
        finally:
            # Clean up container
            if container:
                try:
                    container.stop(timeout=5)
                    container.remove(force=True)
                    logger.info("Container cleaned up successfully")
                except Exception as e:
                    logger.error(f"Failed to clean up container: {str(e)}")
                    try:
                        container.remove(force=True)
                    except:
                        pass
    
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
    
    def _get_install_command(self, language: str, dep_file: str) -> Optional[str]:
        """Get dependency installation command for the language."""
        commands = {
            ("python", "requirements.txt"): "pip install -r requirements.txt",
            ("python", "setup.py"): "pip install -e .",
            ("python", "pyproject.toml"): "pip install .",
            ("javascript", "package.json"): "npm install",
            ("typescript", "package.json"): "npm install",
            ("java", "pom.xml"): "mvn install -DskipTests",
            ("java", "build.gradle"): "gradle build -x test",
            ("go", "go.mod"): "go mod download",
            ("rust", "Cargo.toml"): "cargo build",
            ("ruby", "Gemfile"): "bundle install",
            ("php", "composer.json"): "composer install"
        }
        return commands.get((language, dep_file))
