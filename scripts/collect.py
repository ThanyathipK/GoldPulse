"""Policy-aware collector scaffold for a user-approved JSON endpoint."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests


def robots_allows(url: str, agent: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser(robots_url)
    parser.read()
    return parser.can_fetch(agent, url)


def collect(url: str, output_dir: Path, delay: float = 2.0) -> Path:
    agent = "GoldPulse-Educational/0.1 (contact: configure-before-use)"
    if not robots_allows(url, agent):
        raise PermissionError(f"robots.txt does not allow collection from {url}")
    output_dir.mkdir(parents=True, exist_ok=True)
    time.sleep(max(delay, 1.0))
    response = requests.get(url, headers={"User-Agent": agent}, timeout=20)
    response.raise_for_status()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"response_{stamp}.json"
    payload = {"source_url": url, "collected_at": stamp, "body": response.json()}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch one user-approved JSON source.")
    parser.add_argument("url", help="Documented/public JSON endpoint reviewed by the user")
    parser.add_argument("--output", default="data/raw")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()
    print(collect(args.url, Path(args.output), args.delay))

