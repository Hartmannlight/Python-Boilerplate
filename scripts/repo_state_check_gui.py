from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.stdout.strip()


def is_ci() -> bool:
    return (
        os.environ.get('CI') == 'true'
        or 'GITHUB_ACTIONS' in os.environ
        or 'GITLAB_CI' in os.environ
    )


def repo_root() -> Path:
    out = run(['git', 'rev-parse', '--show-toplevel'])
    return Path(out) if out else Path('.')


def main() -> int:
    if is_ci():
        return 0

    # No GUI popup (boilerplate-safe)
    return 0


if __name__ == '__main__':
    sys.exit(main())
