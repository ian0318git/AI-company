"""MCP tools for code quality and git automation."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ai_embedded_company.mcp._base import _api_call


def register_tools(mcp):
    """Register code quality tools with the FastMCP instance."""

    @mcp.tool()
    async def code_git_auto_commit(
        project_dir: str = ".",
        message: str = "",
        files: str = "",
    ) -> dict:
        """Automatically stage and commit changes to git.

        Args:
            project_dir: Path to the git repository (default: current directory)
            message: Commit message. Auto-generates if empty.
            files: Specific files to add (space-separated). Adds all if empty.
        """
        repo = Path(project_dir).resolve()
        if not (repo / ".git").exists():
            return {"error": "Not a git repository. Initialize with: git init"}

        try:
            # Stage files
            if files:
                file_list = files.split()
                subprocess.run(
                    ["git", "add"] + file_list,
                    cwd=str(repo), capture_output=True, text=True, check=True,
                )
            else:
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=str(repo), capture_output=True, text=True, check=True,
                )

            # Check if there are staged changes
            status = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=str(repo), capture_output=True,
            )
            if status.returncode == 0:
                return {"message": "No changes to commit."}

            # Generate commit message if not provided
            if not message:
                diff = subprocess.run(
                    ["git", "diff", "--cached", "--stat"],
                    cwd=str(repo), capture_output=True, text=True,
                )
                message = f"Auto-commit: changes across multiple files\n\n{diff.stdout[:500]}"

            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=str(repo), capture_output=True, text=True, check=True,
            )

            return {
                "success": True,
                "message": "Changes committed.",
                "commit_message": message[:200],
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Git command failed: {e.stderr}",
            }

    @mcp.tool()
    async def code_review_request(
        project_dir: str = ".",
        focus: str = "",
    ) -> dict:
        """Request a code review of current changes.

        Triggers the code-reviewer agent to review staged/unstaged changes.

        Args:
            project_dir: Path to the git repository (default: current directory)
            focus: What to focus on: all, staged, security, performance, embedded
        """
        repo = Path(project_dir).resolve()

        try:
            # Get diff
            if focus == "staged":
                cmd = ["git", "diff", "--cached"]
            else:
                cmd = ["git", "diff"]

            diff_result = subprocess.run(
                cmd, cwd=str(repo), capture_output=True, text=True,
            )

            if not diff_result.stdout.strip():
                return {"message": "No changes to review.", "focus": focus}

            changed = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=str(repo), capture_output=True, text=True,
            )
            changed_files = [f for f in changed.stdout.strip().split("\n") if f]

            return {
                "status": "review_requested",
                "files_changed": changed_files,
                "file_count": len(changed_files),
                "diff_size": len(diff_result.stdout),
                "focus": focus or "all",
                "message": (
                    f"Code review requested for {len(changed_files)} files. "
                    "The code-reviewer agent should examine these changes."
                ),
            }
        except subprocess.CalledProcessError as e:
            return {"error": f"Git command failed: {e.stderr}"}

    @mcp.tool()
    async def build_check(
        project_dir: str = ".",
        build_type: str = "platformio",
    ) -> dict:
        """Verify that the project compiles/builds without errors.

        Args:
            project_dir: Path to the project
            build_type: Build system: platformio, cargo, npm, make
        """
        repo = Path(project_dir).resolve()
        build_cmds = {
            "platformio": ["platformio", "run"],
            "cargo": ["cargo", "build"],
            "npm": ["npm", "run", "build"],
            "make": ["make"],
        }

        cmd = build_cmds.get(build_type, build_cmds["platformio"])

        try:
            result = subprocess.run(
                cmd, cwd=str(repo), capture_output=True, text=True, timeout=120,
            )
            return {
                "success": result.returncode == 0,
                "build_type": build_type,
                "output_tail": result.stdout[-2000:] if result.stdout else "",
                "error_tail": result.stderr[-1000:] if result.stderr else "",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Build timed out after 120 seconds.",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Build tool '{build_type}' not found.",
            }
