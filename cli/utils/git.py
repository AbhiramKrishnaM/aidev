"""Shared git plumbing used by git-aware commands."""

import subprocess
from typing import List


def run_git_command(cmd: List[str]) -> str:
    """Run a git command and return its output."""
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output}"
