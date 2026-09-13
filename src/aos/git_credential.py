"""Git credential helper for autonomous GitHub App token minting.

Used by git to transparently authenticate pushes as the GitHub App bot:
agent-operating-substrate-agent[bot]
"""

from __future__ import annotations
import sys
from aos.app_auth import get_installation_token


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == 'get':
        token = get_installation_token()
        sys.stdout.write(f'username=x-access-token\npassword={token}\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
