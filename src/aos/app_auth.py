"""GitHub App autonomous authentication and token minting.

Mints short-lived installation access tokens for the autonomous bot identity
(agent-operating-substrate-agent[bot]) to ensure 100% anonymous Git pushes
and webhook attribution with zero connection to personal accounts.
"""

from __future__ import annotations
import base64
import json
from pathlib import Path
import time
from typing import Any, Optional
import urllib.error
import urllib.request

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

DEFAULT_APP_ID = '4930297'
DEFAULT_INSTALLATION_ID = 161365529
DEFAULT_KEY_PATH = Path.home() / '.ssh' / 'agent-operating-substrate-agent.private-key.pem'


def generate_app_jwt(app_id: str = DEFAULT_APP_ID, key_path: Path | str = DEFAULT_KEY_PATH) -> str:
    path = Path(key_path)
    if not path.is_file():
        raise FileNotFoundError(f'GitHub App private key not found at {path}')

    with path.open('rb') as f:
        private_key = load_pem_private_key(f.read(), password=None)

    now = int(time.time())
    header = {'alg': 'RS256', 'typ': 'JWT'}
    payload = {
        'iat': now - 60,
        'exp': now + 540,
        'iss': str(app_id),
    }

    def b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

    header_b64 = b64url(json.dumps(header).encode('utf-8'))
    payload_b64 = b64url(json.dumps(payload).encode('utf-8'))
    signing_input = f'{header_b64}.{payload_b64}'.encode('utf-8')

    signature = private_key.sign(
        signing_input,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return f'{header_b64}.{payload_b64}.{b64url(signature)}'


def get_installation_token(
    installation_id: int = DEFAULT_INSTALLATION_ID,
    app_id: str = DEFAULT_APP_ID,
    key_path: Path | str = DEFAULT_KEY_PATH,
) -> str:
    jwt_token = generate_app_jwt(app_id=app_id, key_path=key_path)
    url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'agent-operating-substrate-agent[bot]',
        },
        method='POST',
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return str(data['token'])


def get_authenticated_remote_url(
    repo_slug: str = 'agent-operating-substrate/agent-operating-substrate',
    installation_id: int = DEFAULT_INSTALLATION_ID,
    app_id: str = DEFAULT_APP_ID,
    key_path: Path | str = DEFAULT_KEY_PATH,
) -> str:
    token = get_installation_token(installation_id=installation_id, app_id=app_id, key_path=key_path)
    return f'https://x-access-token:{token}@github.com/{repo_slug}.git'
