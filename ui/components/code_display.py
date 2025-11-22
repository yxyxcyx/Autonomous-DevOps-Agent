"""Code display components for the UI."""

import streamlit as st
from typing import List, Dict, Any
from datetime import datetime


def render_code_diff(patches: List[Dict[str, Any]]) -> None:
    """
    Render code patches with syntax highlighting.
    
    Args:
        patches: List of patch dictionaries
    """
    st.markdown("###  Generated Patches")
    
    if not patches:
        st.info("No patches generated yet...")
        return
    
    for i, patch in enumerate(patches):
        attempt = patch.get('attempt', i + 1)
        filename = patch.get('filename', 'unknown')
        timestamp = patch.get('timestamp', 0)
        
        # Create expander with metadata
        expander_title = f"Attempt {attempt} - {filename}"
        if timestamp:
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            expander_title += f" ({time_str})"
        
        with st.expander(expander_title, expanded=(i == len(patches) - 1)):
            # Explanation
            explanation = patch.get('explanation', '')
            if explanation:
                st.markdown("** Explanation:**")
                st.info(explanation)
            
            # Code display with syntax highlighting
            code = patch.get('code', '')
            if code:
                st.markdown("** Code:**")
                
                # Detect language from filename
                language = detect_language(filename)
                st.code(code, language=language, line_numbers=True)
            
            # Dependencies
            dependencies = patch.get('dependencies', {})
            if dependencies:
                st.markdown("** Dependencies:**")
                for dep_file, content in dependencies.items():
                    st.text(f"{dep_file}:")
                    st.code(content, language="text")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    label=" Download",
                    data=code,
                    file_name=filename,
                    mime="text/plain",
                    key=f"download_{i}"
                )
            with col2:
                if st.button(" Copy", key=f"copy_{i}"):
                    st.write("Code copied to clipboard!")  # Note: Real copy requires JS
            with col3:
                if st.button(" Analyze", key=f"analyze_{i}"):
                    analyze_code_quality(code, language)


def render_test_results(test_results: List[Dict[str, Any]]) -> None:
    """
    Render test execution results.
    
    Args:
        test_results: List of test result dictionaries
    """
    st.markdown("###  Test Results")
    
    if not test_results:
        st.info("No test results yet...")
        return
    
    # Summary metrics
    total_tests = len(test_results)
    passed_tests = sum(1 for t in test_results if t.get('success'))
    failed_tests = total_tests - passed_tests
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tests", total_tests)
    with col2:
        st.metric(" Passed", passed_tests)
    with col3:
        st.metric(" Failed", failed_tests)
    with col4:
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        st.metric("Pass Rate", f"{pass_rate:.1f}%")
    
    st.markdown("---")
    
    # Individual test results
    for i, result in enumerate(test_results):
        success = result.get('success', False)
        attempt = result.get('attempt', i + 1)
        
        # Status icon and color
        status_icon = "" if success else ""
        status_text = "PASSED" if success else "FAILED"
        status_color = "#4CAF50" if success else "#F44336"
        
        # Create expander for each test
        with st.expander(
            f"{status_icon} Attempt {attempt} - {status_text}",
            expanded=(not success and i == len(test_results) - 1)
        ):
            # Test metadata
            timestamp = result.get('timestamp', 0)
            if timestamp:
                st.caption(f"⏰ Run at: {datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Output sections
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("** Standard Output:**")
                stdout = result.get('stdout', 'No output')
                if stdout and stdout != 'No output':
                    st.code(stdout, language='text')
                else:
                    st.success("No output (clean execution)")
            
            with col2:
                st.markdown("**️ Standard Error:**")
                stderr = result.get('stderr', 'No errors')
                if stderr and stderr != 'No errors':
                    st.code(stderr, language='text')
                else:
                    st.success("No errors!")
            
            # Error details if failed
            if not success and result.get('error'):
                st.markdown("** Error Details:**")
                st.error(result['error'])


def detect_language(filename: str) -> str:
    """
    Detect programming language from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        Language identifier for syntax highlighting
    """
    extension_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.sql': 'sql',
        '.sh': 'bash',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.json': 'json',
        '.xml': 'xml',
        '.html': 'html',
        '.css': 'css',
        '.md': 'markdown',
    }
    
    for ext, lang in extension_map.items():
        if filename.lower().endswith(ext):
            return lang
    
    return 'text'  # Default


def analyze_code_quality(code: str, language: str) -> None:
    """
    Perform basic code quality analysis.
    
    Args:
        code: Source code to analyze
        language: Programming language
    """
    st.markdown("####  Code Analysis")
    
    lines = code.split('\n')
    
    # Basic metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Lines of Code", len(lines))
    
    with col2:
        non_empty = len([l for l in lines if l.strip()])
        st.metric("Non-empty Lines", non_empty)
    
    with col3:
        comment_lines = count_comment_lines(lines, language)
        st.metric("Comment Lines", comment_lines)
    
    # Complexity indicators
    st.markdown("**Complexity Indicators:**")
    
    complexity_metrics = {
        "Functions/Methods": count_functions(code, language),
        "Classes": count_classes(code, language),
        "Imports": count_imports(code, language),
        "Loops": code.count('for ') + code.count('while '),
        "Conditionals": code.count('if ') + code.count('elif ') + code.count('else:'),
    }
    
    for metric, count in complexity_metrics.items():
        st.write(f"- {metric}: {count}")
    
    # Code style warnings
    warnings = check_code_style(code, language)
    if warnings:
        st.warning("**️ Style Warnings:**")
        for warning in warnings:
            st.write(f"- {warning}")


def count_comment_lines(lines: List[str], language: str) -> int:
    """Count comment lines based on language."""
    count = 0
    comment_chars = {
        'python': '#',
        'javascript': '//',
        'java': '//',
        'go': '//',
        'rust': '//',
        'ruby': '#',
        'php': '//',
        'c': '//',
        'cpp': '//',
    }
    
    comment_char = comment_chars.get(language, '#')
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(comment_char):
            count += 1
    
    return count


def count_functions(code: str, language: str) -> int:
    """Count functions/methods in code."""
    function_keywords = {
        'python': ['def ', 'async def '],
        'javascript': ['function ', 'const ', '=>'],
        'java': ['public ', 'private ', 'protected '],
        'go': ['func '],
        'rust': ['fn '],
    }
    
    keywords = function_keywords.get(language, ['def '])
    count = 0
    
    for keyword in keywords:
        count += code.count(keyword)
    
    return count


def count_classes(code: str, language: str) -> int:
    """Count classes in code."""
    class_keywords = {
        'python': 'class ',
        'javascript': 'class ',
        'java': 'class ',
        'typescript': 'class ',
    }
    
    keyword = class_keywords.get(language, 'class ')
    return code.count(keyword)


def count_imports(code: str, language: str) -> int:
    """Count import statements."""
    import_keywords = {
        'python': ['import ', 'from '],
        'javascript': ['import ', 'require('],
        'java': ['import '],
        'go': ['import '],
    }
    
    keywords = import_keywords.get(language, ['import '])
    count = 0
    
    for keyword in keywords:
        count += code.count(keyword)
    
    return count


def check_code_style(code: str, language: str) -> List[str]:
    """Check for basic code style issues."""
    warnings = []
    
    lines = code.split('\n')
    
    # Check for very long lines
    long_lines = [i for i, line in enumerate(lines, 1) if len(line) > 120]
    if long_lines:
        warnings.append(f"Long lines (>120 chars) at: {long_lines[:5]}")
    
    # Check for trailing whitespace
    trailing_whitespace = [i for i, line in enumerate(lines, 1) if line.endswith(' ')]
    if trailing_whitespace:
        warnings.append(f"Trailing whitespace at lines: {trailing_whitespace[:5]}")
    
    # Check for TODO/FIXME comments
    if 'TODO' in code:
        warnings.append("Contains TODO comments")
    if 'FIXME' in code:
        warnings.append("Contains FIXME comments")
    
    # Language-specific checks
    if language == 'python':
        # Check for missing docstrings
        if 'def ' in code and '"""' not in code:
            warnings.append("Functions may be missing docstrings")
    
    return warnings
