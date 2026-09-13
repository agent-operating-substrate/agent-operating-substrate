"""Autonomous Agent Identity and Supervised Mailbox Subsystem.

Provides zero-dependency, free programmatic email accounts for AOS personas via mail.tm REST API.
Credentials are automatically recorded in the local identity vault (.agents/vault/identities.json)
so human supervisors have immediate visibility, passwords, and direct webmail access at https://mail.tm.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import secrets
from typing import Any, Optional
import urllib.error
import urllib.request

API_BASE = "https://api.mail.tm"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "AOS-Substrate/1.0",
}


def get_vault_path(root_dir: Path | str = ".") -> Path:
    """Return path to local identity vault file."""
    root = Path(root_dir)
    vault_dir = root / ".agents" / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    return vault_dir / "identities.json"


def list_identities(root_dir: Path | str = ".") -> list[dict[str, Any]]:
    """Retrieve all autonomous agent identities from vault."""
    vault_file = get_vault_path(root_dir)
    if not vault_file.is_file():
        return []
    try:
        return json.loads(vault_file.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_identity(identity: dict[str, Any], root_dir: Path | str = ".") -> None:
    """Save or update an autonomous agent identity in the vault."""
    identities = list_identities(root_dir)
    # Update existing by persona or append
    idx = next((i for i, item in enumerate(identities) if item.get("persona") == identity.get("persona")), -1)
    if idx >= 0:
        identities[idx] = identity
    else:
        identities.append(identity)

    vault_file = get_vault_path(root_dir)
    vault_file.write_text(json.dumps(identities, indent=2), encoding="utf-8")


def _http_request(url: str, method: str = "GET", data: Optional[dict[str, Any]] = None, token: Optional[str] = None) -> tuple[int, Any]:
    """Execute HTTP request using standard library urllib."""
    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except Exception:
            return exc.code, raw


def get_available_domain() -> str:
    """Fetch active domain for mail.tm account generation."""
    status, data = _http_request(f"{API_BASE}/domains")
    if status == 200 and isinstance(data, dict):
        members = data.get("hydra:member", [])
        for m in members:
            if m.get("isActive") and not m.get("isPrivate"):
                return str(m.get("domain"))
    raise RuntimeError("No public mail.tm domain available currently.")


def create_agent_account(
    persona: str = "maintainer",
    password: Optional[str] = None,
    domain: Optional[str] = None,
    root_dir: Path | str = ".",
) -> dict[str, Any]:
    """Create a free programmatic email account and register it in the supervisory vault."""
    active_domain = domain if domain else get_available_domain()
    persona_key = persona if persona.startswith("aos-agent-") else f"aos-agent-{persona}"
    clean_suffix = secrets.token_hex(4)
    address = f"{persona_key}-{clean_suffix}@{active_domain}".lower()
    pw = password if password else secrets.token_urlsafe(16)

    # 1. Register Account with retry for rate limiting
    import time
    status_reg, data_reg = 0, {}
    for _ in range(3):
        status_reg, data_reg = _http_request(
            f"{API_BASE}/accounts",
            method="POST",
            data={"address": address, "password": pw},
        )
        if status_reg in (200, 201):
            break
        time.sleep(2.0)

    if status_reg not in (200, 201):
        raise RuntimeError(f"Failed to register mailbox on mail.tm: {data_reg}")

    account_id = data_reg.get("id", "")

    # 2. Authenticate to obtain token
    status_auth, data_auth = _http_request(
        f"{API_BASE}/token",
        method="POST",
        data={"address": address, "password": pw},
    )
    token = data_auth.get("token", "") if status_auth == 200 and isinstance(data_auth, dict) else ""

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    identity_record = {
        "persona": persona_key,
        "name": f"AOS Agent ({persona.capitalize()})",
        "handle": persona_key,
        "address": address,
        "password": pw,
        "token": token,
        "account_id": account_id,
        "domain": active_domain,
        "webmail_url": "https://mail.tm",
        "created_at": now_iso,
        "supervision_instructions": f"Visit https://mail.tm and log in with email '{address}' and password to supervise this mailbox directly.",
    }

    save_identity(identity_record, root_dir=root_dir)
    return identity_record


def fetch_agent_messages(persona_or_address: str, root_dir: Path | str = ".") -> list[dict[str, Any]]:
    """Fetch incoming messages for a supervised agent identity."""
    identities = list_identities(root_dir)
    match = next(
        (
            item for item in identities
            if item.get("persona") == persona_or_address
            or item.get("address") == persona_or_address
            or item.get("handle") == persona_or_address
        ),
        None,
    )
    if not match:
        raise ValueError(f"Identity '{persona_or_address}' not found in supervisor vault.")

    token = match.get("token")
    address = match.get("address")
    pw = match.get("password")

    # Refresh token if needed
    status, data = _http_request(f"{API_BASE}/messages", token=token)
    if status in (401, 403) and address and pw:
        status_auth, data_auth = _http_request(
            f"{API_BASE}/token",
            method="POST",
            data={"address": address, "password": pw},
        )
        if status_auth == 200 and isinstance(data_auth, dict):
            token = data_auth.get("token", "")
            match["token"] = token
            save_identity(match, root_dir=root_dir)
            status, data = _http_request(f"{API_BASE}/messages", token=token)

    if status == 200 and isinstance(data, dict):
        return data.get("hydra:member", [])
    return []


def fetch_message_detail(persona_or_address: str, message_id: str, root_dir: Path | str = ".") -> dict[str, Any]:
    """Fetch full body content for a specific message."""
    identities = list_identities(root_dir)
    match = next(
        (
            item for item in identities
            if item.get("persona") == persona_or_address
            or item.get("address") == persona_or_address
        ),
        None,
    )
    if not match:
        raise ValueError(f"Identity '{persona_or_address}' not found in supervisor vault.")

    token = match.get("token")
    status, data = _http_request(f"{API_BASE}/messages/{message_id}", token=token)
    if status == 200 and isinstance(data, dict):
        return data
    return {}
