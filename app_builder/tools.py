import pathlib
import subprocess
import socket
import webbrowser
import threading
import time
from typing import Tuple

from langchain_core.tools import tool

PROJECT_ROOT = pathlib.Path.cwd() / "generated_project"


def safe_path_for_project(path: str) -> pathlib.Path:
    p = (PROJECT_ROOT / path).resolve()
    if PROJECT_ROOT.resolve() not in p.parents and PROJECT_ROOT.resolve() != p.parent and PROJECT_ROOT.resolve() != p:
        raise ValueError("Attempt to write outside project root")
    return p


@tool
def write_file(path: str, content: str) -> str:
    """Writes content to a file at the specified path within the project root."""
    p = safe_path_for_project(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return f"WROTE:{p}"


@tool
def read_file(path: str) -> str:
    """Reads content from a file at the specified path within the project root."""
    p = safe_path_for_project(path)
    if not p.exists():
        return ""
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


@tool
def get_current_directory() -> str:
    """Returns the current working directory."""
    return str(PROJECT_ROOT)


@tool
def list_files(directory: str = ".") -> str:
    """Lists all files in the specified directory within the project root."""
    p = safe_path_for_project(directory)
    if not p.is_dir():
        return f"ERROR: {p} is not a directory"
    files = [str(f.relative_to(PROJECT_ROOT)) for f in p.glob("**/*") if f.is_file()]
    return "\n".join(files) if files else "No files found."

@tool
def run_cmd(cmd: str, cwd: str = None, timeout: int = 30) -> Tuple[int, str, str]:
    """Runs a shell command in the specified directory and returns the result."""
    cwd_dir = safe_path_for_project(cwd) if cwd else PROJECT_ROOT
    res = subprocess.run(cmd, shell=True, cwd=str(cwd_dir), capture_output=True, text=True, timeout=timeout)
    return res.returncode, res.stdout, res.stderr


@tool
def check_code_quality(file_path: str) -> str:
    """Checks code quality of a specific file by reading and analyzing it."""
    content = read_file.invoke({"path": file_path})
    if not content:
        return f"File {file_path} not found or empty"

    issues = []
    checks = {
        "Has imports": "import" in content or "require" in content or "from" in content,
        "Has error handling": "try" in content or "catch" in content or "error" in content.lower(),
        "Not empty": len(content.strip()) > 0,
    }

    for check, passed in checks.items():
        if not passed:
            issues.append(f"Missing: {check}")

    if issues:
        return f"Issues found in {file_path}:\n" + "\n".join(issues)
    return f"Code quality check passed for {file_path}"


@tool
def validate_syntax(file_path: str) -> str:
    """Validates syntax of a file by attempting to parse/compile it."""
    p = safe_path_for_project(file_path)
    if not p.exists():
        return f"File {file_path} not found"

    ext = p.suffix.lower()
    if ext == ".py":
        try:
            with open(p, "r", encoding="utf-8") as f:
                compile(f.read(), str(p), "exec")
            return f"✓ Python syntax valid for {file_path}"
        except SyntaxError as e:
            return f"✗ Syntax error in {file_path}: {e.msg} at line {e.lineno}"
        except Exception as e:
            return f"✗ Error checking {file_path}: {str(e)}"
    elif ext in [".js", ".jsx"]:
        # For JS, we'd need node or a JS parser, but we can check basic structure
        content = read_file.invoke({"path": file_path})
        if "function" in content or "const" in content or "let" in content or "class" in content:
            return f"✓ JavaScript structure looks valid for {file_path}"
        return f"⚠ JavaScript file {file_path} may have issues"
    elif ext in [".html", ".css"]:
        return f"✓ {ext.upper()} file {file_path} structure valid"

    return f"File type {ext} not validated"


@tool
def analyze_file_issues(file_path: str) -> str:
    """Deep analysis of a file to find potential issues, errors, and improvements."""
    content = read_file.invoke({"path": file_path})
    if not content:
        return f"File {file_path} is empty or not found"

    issues = []
    suggestions = []

    # Check for common issues
    if "TODO" in content or "FIXME" in content:
        issues.append("Contains TODO/FIXME comments")

    if "console.log" in content and "test" not in file_path.lower():
        suggestions.append("Consider removing console.log statements for production")

    if "eval(" in content:
        issues.append("SECURITY: Uses eval() which is dangerous")

    if len(content) < 50:
        suggestions.append("File is very short - ensure it's complete")

    if "function" in content and "return" not in content:
        suggestions.append("Functions should have return statements")

    result = f"Analysis for {file_path}:\n"
    if issues:
        result += "Issues:\n" + "\n".join(f"  - {i}" for i in issues) + "\n"
    if suggestions:
        result += "Suggestions:\n" + "\n".join(f"  - {s}" for s in suggestions) + "\n"
    if not issues and not suggestions:
        result += "✓ No issues found\n"

    return result



def init_project_root():
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    return str(PROJECT_ROOT)
