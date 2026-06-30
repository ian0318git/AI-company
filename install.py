#!/usr/bin/env python3
"""AI Embedded Company — One-Click Installer.

Installs the full system:
  1. Checks Python >= 3.11, Node.js (optional)
  2. Installs Python dependencies
  3. Registers the MCP server globally
  4. Registers lifecycle hooks
  5. Copies agent templates to ~/.claude/agents/
  6. Verifies the installation
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_command(cmd: str) -> bool:
    """Check if a command exists on the system PATH."""
    return shutil.which(cmd) is not None


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a command with error handling."""
    is_windows = sys.platform == "win32"
    shell = is_windows and any(x in str(args[0]) for x in ("npm", "npx"))

    try:
        result = subprocess.run(
            args, cwd=cwd, shell=shell,
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            print(f"  [WARN] Command failed: {' '.join(args)}")
            if result.stderr:
                print(f"    {result.stderr.strip()[:200]}")
        return result
    except FileNotFoundError:
        print(f"  [WARN] Command not found: {args[0]}")
        return subprocess.CompletedProcess(args, -1, "", "command not found")


def _hook_command_exists(hooks: dict, fragment: str) -> bool:
    """Check if a hook with this command fragment already exists."""
    for group_name, group_hooks in hooks.items():
        if not isinstance(group_hooks, list):
            continue
        for hook in group_hooks:
            if isinstance(hook, dict) and fragment in hook.get("command", ""):
                return True
    return False


def register_hooks(project_root: Path) -> None:
    """Register lifecycle hooks in ~/.claude/settings.json."""
    settings_path = Path.home() / ".claude" / "settings.json"
    if not settings_path.exists():
        print("  [SKIP] No Claude Code settings.json found")
        return

    with open(settings_path) as f:
        try:
            settings = json.load(f)
        except json.JSONDecodeError:
            settings = {}

    hooks = settings.get("hooks", {})
    modified = False

    python = sys.executable
    hooks_dir = project_root / "src" / "ai_embedded_company" / "hooks"
    hook_group = "ai-embedded-company"

    # Ensure the hooks directory exists
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Define hooks to register
    hook_scripts = {
        "SessionStart": "session_bootstrap.py",
        "SessionEnd": "send_event.py",
        "SubagentStart": "inject_context.py",
        "SubagentStop": "send_event.py",
        "PreToolUse": "guardrails.py",
        "PostToolUse": "send_event.py",
        "UserPromptSubmit": "context_monitor.py",
        "Stop": "send_event.py",
        "PreCompact": "pre_compact_save.py",
    }

    registered = 0
    for event, script in hook_scripts.items():
        script_path = hooks_dir / script
        if not script_path.exists():
            continue  # Skip scripts not yet created

        command = f"{python} {script_path}"
        if _hook_command_exists(hooks, script):
            continue

        if hook_group not in hooks:
            hooks[hook_group] = []

        if not isinstance(hooks[hook_group], list):
            hooks[hook_group] = []

        hooks[hook_group].append({
            "event": event,
            "command": command,
        })
        registered += 1

    if registered > 0:
        settings["hooks"] = hooks
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        print(f"  [OK] Registered {registered} hooks")
    else:
        print("  [OK] Hooks already registered (or scripts not yet available)")


def copy_agent_templates(project_root: Path, overwrite: bool = False) -> None:
    """Copy agent .md templates to ~/.claude/agents/."""
    agents_src = project_root / "plugin" / "agents"
    agents_dst = Path.home() / ".claude" / "agents"

    if not agents_src.exists():
        print("  [SKIP] No agent templates found")
        return

    agents_dst.mkdir(parents=True, exist_ok=True)

    copied = 0
    for md_file in agents_src.glob("*.md"):
        dst_file = agents_dst / md_file.name
        if dst_file.exists() and not overwrite:
            continue
        shutil.copy2(md_file, dst_file)
        copied += 1

    if copied > 0:
        print(f"  [OK] Copied {copied} agent templates")
    else:
        print("  [OK] Agent templates already up to date")


def register_global_mcp(project_root: Path) -> None:
    """Register the MCP server globally via claude mcp add-json or direct config."""
    # Try claude mcp add-json first
    mcp_entry = {
        "name": "ai-embedded-company",
        "command": sys.executable,
        "args": ["-m", "ai_embedded_company.mcp.server"],
    }

    if check_command("claude"):
        result = run([
            "claude", "mcp", "add-json",
            "--scope", "global",
            json.dumps(mcp_entry),
        ])
        if result.returncode == 0:
            print("  [OK] MCP server registered globally via 'claude mcp add-json'")
            return

    # Fallback: write directly to ~/.claude.json
    claude_config = Path.home() / ".claude.json"
    if claude_config.exists():
        with open(claude_config) as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}

        mcps = config.get("mcpServers", {})
        mcps["ai-embedded-company"] = {
            "command": sys.executable,
            "args": ["-m", "ai_embedded_company.mcp.server"],
        }
        config["mcpServers"] = mcps

        with open(claude_config, "w") as f:
            json.dump(config, f, indent=2)
        print("  [OK] MCP server registered in ~/.claude.json")
    else:
        # Create project-level .mcp.json fallback
        mcp_file = Path.cwd() / ".mcp.json"
        mcp_file.write_text(json.dumps({"mcpServers": {"ai-embedded-company": {
            "command": sys.executable,
            "args": ["-m", "ai_embedded_company.mcp.server"],
        }}}, indent=2))
        print("  [OK] MCP server registered in project .mcp.json")


def verify_installation(project_root: Path) -> None:
    """Run verification checks and print results."""
    print()
    print("── Verification ──")

    checks = []

    # 1. Global MCP
    claude_config = Path.home() / ".claude.json"
    mcp_found = False
    if claude_config.exists():
        try:
            config = json.loads(claude_config.read_text())
            mcp_found = "ai-embedded-company" in config.get("mcpServers", {})
        except Exception:
            pass
    checks.append(("Global MCP registered", mcp_found))

    # 2. Project MCP fallback
    mcp_json = Path.cwd() / ".mcp.json"
    checks.append(("Project .mcp.json exists", mcp_json.exists()))

    # 3. Agent templates
    agents_dir = Path.home() / ".claude" / "agents"
    agent_count = len(list(agents_dir.glob("*.md"))) if agents_dir.exists() else 0
    checks.append((f"Agent templates ({agent_count} files)", agent_count > 0))

    # 4. Python package
    pkg_ok = project_root.joinpath("src", "ai_embedded_company").exists()
    checks.append(("Package directory", pkg_ok))

    for name, ok in checks:
        status = "[OK]" if ok else "[WARN]"
        print(f"  {status} {name}")


def main():
    """Run the full installation."""
    project_root = Path(__file__).parent.resolve()

    print("╔══════════════════════════════════════╗")
    print("║  AI Embedded Company — Installer    ║")
    print("╚══════════════════════════════════════╝")
    print()

    # Check Python version
    python_ver = sys.version_info[:2]
    if python_ver < (3, 11):
        print(f"[FAIL] Python 3.11+ required, found {sys.version}")
        sys.exit(1)
    print(f"[OK] Python {sys.version}")

    # Check Node.js (optional)
    has_node = check_command("node")
    if not has_node:
        print("[WARN] Node.js not found — dashboard will not be built (optional)")

    # Check pip
    if not check_command("pip") and not check_command("pip3"):
        print("[WARN] pip not found — dependency installation may fail")

    print()
    print("── Installing dependencies ──")
    run([sys.executable, "-m", "pip", "install", "-e", ".", "--quiet"], cwd=project_root)

    print()
    print("── Registering MCP server ──")
    register_global_mcp(project_root)

    print()
    print("── Registering hooks ──")
    register_hooks(project_root)

    print()
    print("── Copying agent templates ──")
    copy_agent_templates(project_root)

    # Create data directory
    data_dir = Path.home() / ".claude" / "data" / "ai-embedded-company"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save install path
    install_info = data_dir / ".install.json"
    install_info.write_text(json.dumps({
        "install_path": str(project_root),
        "version": "0.1.0",
    }, indent=2))

    verify_installation(project_root)

    print()
    print("── Next Steps ──")
    print(f"  1. Restart Claude Code or reload MCP servers")
    print(f"  2. Test: system_health (MCP tool)")
    print(f"  3. Create your first project: project_create")
    print(f"  4. Start the dashboard (optional): cd dashboard && npm install && npm run dev")
    print()


if __name__ == "__main__":
    main()
