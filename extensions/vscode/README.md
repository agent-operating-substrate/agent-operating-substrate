# AOS Extension for VS Code and Cursor

Seamless companion extension connecting your editor workspace directly to the Agent Operating Substrate.

***

## Features

* **Status Bar Protection Indicator**: Displays active status in the bottom status bar (`$(shield) AOS: Protected`). Click to open the Web Control Plane.
* **Harness Synchronization**: Run `AOS: Sync Guardrails to AI Harnesses` from the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) to compile active invariants into `.cursorrules`, `CLAUDE.md`, `.windsurfrules`, and Copilot configs.
* **Autonomous Ingestion**: Run `AOS: Scan Codebase for Tailored Invariants` to analyze project manifests and synthesize tailored guardrails.
* **File Guardrail Inspector**: Run `AOS: Inspect Active Guardrails for Current File` to view which machine-readable constraints bind AI agents editing the currently open file.
* **Control Plane Launcher**: 1-click access to the full visual dashboard at `http://127.0.0.1:8484`.

***

## Installation & Local Testing

To test this extension locally in Cursor or VS Code:

1. Open Cursor or VS Code.
2. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
3. Select `Developer: Install Extension from Location...` or copy `extensions/vscode/` to your `~/.vscode/extensions/` (or `~/.cursor/extensions/`) folder.
4. The extension activates automatically when a workspace with `.agents/` is opened.
