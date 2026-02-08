#!/usr/bin/env python3
"""Envía el diff actual al gateway biométrico para que ejecute el escaneo IA."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

DEFAULT_GATEWAY_URL = os.environ.get('BIOMETRIC_GATEWAY_URL',
                                     'http://localhost:7000').rstrip('/')
SCAN_ENDPOINT = '/api/security/ci-scan'
TIMEOUT = float(os.environ.get('CI_GATEWAY_TIMEOUT', '12'))


def run_git_diff() -> str:
    repo = Path(__file__).resolve().parents[1]
    try:
        diff = subprocess.run(
            ['git', '-C', str(repo), 'diff', '--unified=0', 'HEAD~1'],
            check=False,
            capture_output=True,
            text=True,
            encoding='utf-8')
        output = diff.stdout.strip()
        if not output:
            fallback = subprocess.run(
                ['git', '-C', str(repo), 'show', 'HEAD', '--stat'],
                check=False,
                capture_output=True,
                text=True,
                encoding='utf-8')
            output = fallback.stdout.strip()
        return output or 'No diff disponible'
    except FileNotFoundError:
        return 'Git no disponible en runner'


def main() -> int:
    gateway_url = DEFAULT_GATEWAY_URL
    payload = {
        'event': 'ci.security_scan',
        'repository': os.environ.get('GITHUB_REPOSITORY', 'local'),
        'branch': os.environ.get('GITHUB_REF', 'local'),
        'commit': os.environ.get('GITHUB_SHA'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'actor': os.environ.get('GITHUB_ACTOR'),
        'diff': run_git_diff()[:20000]
    }

    response = requests.post(f"{gateway_url}{SCAN_ENDPOINT}",
                             json=payload,
                             timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()

    print(json.dumps(data, indent=2))

    alert = (data.get('analysis') or {}).get('alert_level')
    if alert in {'CRITICA', 'MEDIA'}:
        print('⚠️  El motor IA marcó el cambio con nivel', alert)
        return 2

    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except requests.RequestException as exc:
        print(f"Error contactando al gateway biométrico: {exc}")
        raise SystemExit(1)
