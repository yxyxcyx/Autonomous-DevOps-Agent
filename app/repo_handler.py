"""Repository handling for cloning and analyzing code."""

import os
import tempfile
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import structlog

MAX_FILE_READ_BYTES = 200_000  # ~200 KB safety cap for direct reads

logger = structlog.get_logger()


class RepositoryHandler:
    """Handles Git repository operations and code analysis."""
    
    def __init__(self):
        self.temp_dirs = []  # Track temp directories for cleanup
    
    def clone_repository(
        self, 
        repository_url: str, 
        branch: str = "main",
        target_dir: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        Clone a Git repository.
        
        Args:
            repository_url: Git repository URL
            branch: Branch to checkout
            target_dir: Target directory (creates temp if None)
            
        Returns:
            Tuple of (success, repo_path, error_message)
        """
        try:
            # Create temp directory if not provided
            if target_dir is None:
                target_dir = tempfile.mkdtemp(prefix="repo_")
                self.temp_dirs.append(target_dir)
            
            logger.info(
                "Cloning repository",
                url=repository_url,
                branch=branch,
                target=target_dir
            )
            
            # Clone the repository
            result = subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", branch, repository_url, target_dir],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                error_msg = f"Git clone failed: {result.stderr}"
                logger.error(error_msg)
                return False, "", error_msg
            
            logger.info("Repository cloned successfully", path=target_dir)
            return True, target_dir, ""
            
        except subprocess.TimeoutExpired:
            error_msg = "Repository cloning timed out after 60 seconds"
            logger.error(error_msg)
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Failed to clone repository: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def analyze_repository(self, repo_path: str) -> Dict[str, any]:
        """
        Analyze repository structure and content.
        
        Args:
            repo_path: Path to the cloned repository
            
        Returns:
            Dictionary with repository analysis
        """
        try:
            analysis = {
                "structure": {},
                "languages": {},
                "file_count": 0,
                "total_lines": 0,
                "main_files": [],
                "test_files": [],
                "config_files": [],
                "readme_content": ""
            }
            
            # Walk through repository
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden and vendor directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'vendor', '__pycache__']]
                
                rel_root = os.path.relpath(root, repo_path)
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    analysis["file_count"] += 1
                    
                    # Categorize files
                    if 'test' in rel_path.lower() or 'spec' in rel_path.lower():
                        analysis["test_files"].append(rel_path)
                    elif file in ['README.md', 'readme.md', 'README.txt']:
                        analysis["readme_content"] = self._read_file_safe(file_path)
                    elif file.endswith(('.json', '.yaml', '.yml', '.toml', '.ini', '.cfg')):
                        analysis["config_files"].append(rel_path)
                    else:
                        analysis["main_files"].append(rel_path)
                    
                    # Count language usage
                    ext = os.path.splitext(file)[1]
                    if ext:
                        analysis["languages"][ext] = analysis["languages"].get(ext, 0) + 1
                    
                    # Count lines (for text files)
                    if self._is_text_file(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                analysis["total_lines"] += sum(1 for _ in f)
                        except:
                            pass
            
            # Build directory structure
            analysis["structure"] = self._build_tree_structure(repo_path)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze repository: {str(e)}")
            return {"error": str(e)}
    
    def get_file_content(
        self, 
        repo_path: str, 
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        max_bytes: int = MAX_FILE_READ_BYTES
    ) -> Optional[str]:
        """
        Get content of a specific file in the repository.
        
        Args:
            repo_path: Path to repository
            file_path: Relative path to file
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (1-indexed)
            
        Returns:
            File content or None if error
        """
        try:
            full_path = os.path.join(repo_path, file_path)
            
            if not os.path.exists(full_path):
                logger.warning(f"File not found: {file_path}")
                return None
            
            file_size = os.path.getsize(full_path)

            if start_line is not None and end_line is not None:
                # Stream only the requested window to avoid loading entire file
                selected_lines = []
                start_idx = max(0, start_line - 1)
                end_idx = max(start_idx, end_line)
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for current_line, line_content in enumerate(f):
                        if current_line > end_idx:
                            break
                        if start_idx <= current_line < end_idx:
                            selected_lines.append(line_content)
                            if sum(len(l) for l in selected_lines) >= max_bytes:
                                selected_lines.append("\n[Truncated view due to size limit]\n")
                                break
                return ''.join(selected_lines)

            if file_size > max_bytes:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_bytes)
                return f"{content}\n[Truncated to {max_bytes} bytes from {file_size} bytes]"

            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
            
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}")
            return None
    
    def find_files_by_pattern(
        self, 
        repo_path: str, 
        pattern: str,
        file_extensions: Optional[List[str]] = None
    ) -> List[str]:
        """
        Find files matching a pattern.
        
        Args:
            repo_path: Path to repository
            pattern: Pattern to search for in filenames
            file_extensions: List of extensions to filter (e.g., ['.py', '.js'])
            
        Returns:
            List of matching file paths
        """
        matching_files = []
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    # Check pattern
                    if pattern.lower() in file.lower():
                        # Check extension if specified
                        if file_extensions:
                            if any(file.endswith(ext) for ext in file_extensions):
                                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                                matching_files.append(rel_path)
                        else:
                            rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                            matching_files.append(rel_path)
                            
        except Exception as e:
            logger.error(f"Failed to find files: {str(e)}")
        
        return matching_files
    
    def search_code(
        self, 
        repo_path: str, 
        search_term: str,
        file_extensions: Optional[List[str]] = None,
        max_results: int = 50
    ) -> List[Dict[str, any]]:
        """
        Search for code patterns in repository.
        
        Args:
            repo_path: Path to repository
            search_term: Term to search for
            file_extensions: File extensions to search
            max_results: Maximum number of results
            
        Returns:
            List of search results with file, line number, and content
        """
        results = []
        
        try:
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'vendor']]
                
                for file in files:
                    if file_extensions and not any(file.endswith(ext) for ext in file_extensions):
                        continue
                    
                    file_path = os.path.join(root, file)
                    if not self._is_text_file(file_path):
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if search_term.lower() in line.lower():
                                    results.append({
                                        "file": os.path.relpath(file_path, repo_path),
                                        "line_number": line_num,
                                        "content": line.strip()
                                    })
                                    
                                    if len(results) >= max_results:
                                        return results
                    except:
                        continue
                        
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
        
        return results
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Failed to cleanup {temp_dir}: {str(e)}")
        self.temp_dirs.clear()
    
    def _is_text_file(self, file_path: str) -> bool:
        """Check if file is a text file."""
        text_extensions = {
            '.py', '.js', '.ts', '.java', '.go', '.rs', '.rb', '.php',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.kt', '.scala',
            '.txt', '.md', '.json', '.yaml', '.yml', '.xml', '.html', '.css',
            '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd'
        }
        return any(file_path.endswith(ext) for ext in text_extensions)
    
    def _read_file_safe(self, file_path: str, max_size: int = 100000) -> str:
        """Safely read a file with size limit."""
        try:
            size = os.path.getsize(file_path)
            if size > max_size:
                return f"[File too large: {size} bytes]"
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            return "[Could not read file]"
    
    def _build_tree_structure(self, repo_path: str, max_depth: int = 3) -> Dict:
        """Build a tree structure of the repository."""
        def build_tree(path: str, depth: int = 0) -> Dict:
            if depth >= max_depth:
                return {"...": "max depth reached"}
            
            tree = {}
            try:
                items = sorted(os.listdir(path))
                for item in items[:50]:  # Limit items per directory
                    if item.startswith('.'):
                        continue
                    
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        if item not in ['node_modules', 'vendor', '__pycache__']:
                            tree[f"{item}/"] = build_tree(item_path, depth + 1)
                    else:
                        tree[item] = "file"
            except:
                pass
            
            return tree
        
        return build_tree(repo_path)
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()
