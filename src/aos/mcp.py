"""Model Context Protocol (MCP) server for universal agent harness integration."""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any

from aos.autopsy import inscribe_candidate, synthesize_candidate_rule
from aos.blackboard import post_event, read_events
from aos.engine import RuleEngine
from aos.enforcer import enforce_all

PROTOCOL_VERSION = "2024-11-05"


def get_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "aos_rules_check",
            "description": "Evaluate target file paths against active substrate invariant rules.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to check.",
                    },
                },
                "required": ["files"],
            },
        },
        {
            "name": "aos_rules_list",
            "description": "List all discovered invariant rules in the substrate.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["active", "candidate", "archive"],
                        "description": "Filter by rule status.",
                    },
                },
            },
        },
        {
            "name": "aos_autopsy",
            "description": "Inscribe a new candidate invariant rule derived from a failure autopsy.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Unique rule identifier."},
                    "statement": {"type": "string", "description": "Invariant directive statement."},
                    "rationale": {"type": "string", "description": "Technical justification."},
                    "paths": {"type": "array", "items": {"type": "string"}, "description": "Path globs."},
                    "languages": {"type": "array", "items": {"type": "string"}, "description": "Languages."},
                    "incident_id": {"type": "string", "description": "Incident reference."},
                },
                "required": ["id", "statement", "rationale", "paths"],
            },
        },
        {
            "name": "aos_blackboard_post",
            "description": "Broadcast an event or intent announcement on the local peer blackboard.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Event type."},
                    "sender": {"type": "string", "description": "Agent identifier."},
                    "payload": {"type": "object", "description": "Arbitrary payload mapping."},
                },
                "required": ["type", "sender", "payload"],
            },
        },
    ]


def handle_tool_call(name: str, args: dict[str, Any], root_dir: Path) -> str:
    if name == "aos_rules_check":
        files = args.get("files", [])
        engine = RuleEngine(root_dir=root_dir)
        matches = engine.match_files(files, status="active")
        violations = enforce_all(files, root_dir=root_dir)

        output: dict[str, Any] = {"matches": {}, "violations": []}
        for f, rules in matches.items():
            output["matches"][f] = [r.to_dict() for r in rules]
        output["violations"] = [
            {
                "file_path": v.file_path,
                "rule_id": v.rule_id,
                "message": v.message,
                "enforcement": v.enforcement,
                "line": v.line_number,
            }
            for v in violations
        ]
        return json.dumps(output, indent=2)

    elif name == "aos_rules_list":
        status = args.get("status")
        engine = RuleEngine(root_dir=root_dir)
        rules = engine.get_rules(status=status)
        return json.dumps([r.to_dict() for r in rules], indent=2)

    elif name == "aos_autopsy":
        rule = synthesize_candidate_rule(
            rule_id=args["id"],
            statement=args["statement"],
            rationale=args["rationale"],
            paths=args["paths"],
            languages=args.get("languages", []),
            incident_id=args.get("incident_id", "inc-mcp"),
            inscribing_agent="mcp-client-agent",
        )
        saved = inscribe_candidate(rule, substrate_dir=root_dir / ".agents" / "substrate")
        return json.dumps({"status": "inscribed", "path": str(saved)})

    elif name == "aos_blackboard_post":
        ev = post_event(
            {
                "type": args["type"],
                "sender": args["sender"],
                "payload": args["payload"],
            },
            root_dir=root_dir,
        )
        return json.dumps({"status": "posted", "event_id": ev.event_id})

    return json.dumps({"error": f"Unknown tool: {name}"})


def run_mcp_server(root_dir: Path | str = ".") -> None:
    """Run the JSON-RPC stdio loop."""
    root = Path(root_dir)
    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue
        try:
            req = json.loads(line_str)
        except Exception:
            continue

        msg_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            res = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "aos-mcp-server", "version": "0.2.0"},
                },
            }
        elif method == "tools/list":
            res = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": get_tool_definitions()},
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            text_result = handle_tool_call(tool_name, tool_args, root)
            res = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": text_result}],
                },
            }
        elif method == "notifications/initialized":
            continue
        else:
            res = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        sys.stdout.write(json.dumps(res) + "\n")
        sys.stdout.flush()
