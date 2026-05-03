#!/usr/bin/env python3

"""
Import an Elastic/Kibana Security rule into the rulebook repo.

This script lives alongside the Raycast script, but it still
reads credentials and the rulebook path from:

  /Users/abdullah/work/cipher/rulebook-deployer/config.ini

Only that project is used for config/credentials; all rule
files are written into the rulebook repo pointed to by
rulebook_base_path in the config.
"""

from __future__ import annotations

import configparser
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import urlparse

import requests
import yaml
from requests.auth import HTTPBasicAuth


CONFIG_PATH = Path("/Users/abdullah/work/cipher/rulebook-deployer/config.ini")


@dataclass
class Settings:
    username: str
    password: str
    rulebook_base_path: Path


def load_settings() -> Settings:
    if not CONFIG_PATH.exists():
        raise SystemExit(f"Config file not found: {CONFIG_PATH}")

    parser = configparser.ConfigParser()
    if not parser.read(CONFIG_PATH):
        raise SystemExit(f"Failed to read config file: {CONFIG_PATH}")

    if "default" not in parser:
        raise SystemExit("Missing [default] section in config.ini")

    default = parser["default"]
    try:
        username = default["username"]
        password = default["password"]
        rulebook_raw = default["rulebook_base_path"]
    except KeyError as exc:
        raise SystemExit(f"Missing required config key in [default]: {exc}") from exc

    rulebook_base = Path(os.path.expanduser(rulebook_raw)).resolve()
    if not rulebook_base.exists():
        raise SystemExit(f"rulebook_base_path does not exist: {rulebook_base}")

    return Settings(
        username=username,
        password=password,
        rulebook_base_path=rulebook_base,
    )


def parse_kibana_rule_url(url: str) -> Tuple[str, str]:
    """Return (base_url, rule_id) from a Kibana Security rule URL."""

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise SystemExit(f"Invalid URL (missing scheme or host): {url}")

    path = parsed.path or ""

    # Kibana Security rule URLs typically contain /rules/id/<rule_id>
    m = re.search(r"/rules/id/([^/]+)", path)
    if not m:
        raise SystemExit(
            f"Could not extract rule_id from URL path: {path}\n"
            "Expected a segment like /rules/id/<rule_id>."
        )
    rule_id = m.group(1)

    # Preserve any /s/<space> prefix, strip everything starting from /app/...
    base_path = path
    for marker in ("/app/security", "/app/detections", "/app/siem", "/app"):
        idx = base_path.find(marker)
        if idx != -1:
            base_path = base_path[:idx]
            break

    base_url = f"{parsed.scheme}://{parsed.netloc}{base_path}".rstrip("/")
    return base_url, rule_id


def fetch_rule(
    base_url: str, id: str, settings: Settings
) -> Dict[str, Any]:
    """Fetch rule details from Kibana Detection Engine API."""

    api_url = f"{base_url}/api/detection_engine/rules"
    headers = {
        "kbn-xsrf": "true",
        "Content-Type": "application/json",
    }

    resp = requests.get(
        api_url,
        params={"id": id},
        auth=HTTPBasicAuth(settings.username, settings.password),
        headers=headers,
        timeout=30,
    )

    if resp.status_code != 200:
        body_snippet = resp.text[:500].replace("\n", " ")
        raise SystemExit(
            f"Failed to fetch rule from Kibana:\n"
            f"  URL: {api_url}\n"
            f"  Status: {resp.status_code}\n"
            f"  Body: {body_snippet}"
        )

    try:
        data = resp.json()
    except Exception as exc:
        raise SystemExit(f"Failed to parse Kibana response as JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("Unexpected Kibana response format (expected JSON object).")

    return data


def infer_platform(rule: Dict[str, Any]) -> str:
    """Best-effort guess of platform folder from rule tags."""

    tags = [t.lower() for t in rule.get("tags", []) if isinstance(t, str)]

    if any("linux" in t for t in tags):
        return "linux"
    if any("mac" in t or "darwin" in t or "macos" in t for t in tags):
        return "macos"
    if any("cloud" in t for t in tags):
        return "cloud"
    if any("network" in t for t in tags):
        return "network"
    if any("identity" in t for t in tags):
        return "identity"

    # Fallback default
    return "windows"


def interval_to_cron(interval: str) -> str:
    """
    Convert a simple Elastic interval string like '5m' or '15m' to a cron expression.
    Falls back to the default every-5-minutes schedule if parsing fails.
    """

    interval = (interval or "").strip()
    m = re.fullmatch(r"(\d+)m", interval)
    if not m:
        return "*/5 * * * *"

    minutes = int(m.group(1))
    if minutes <= 0:
        return "*/5 * * * *"

    return f"*/{minutes} * * * *"


def populate_rule_file_from_kibana(rule_path: Path, kibana_rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load an existing rule YAML file and fill it with details from the Kibana rule JSON.
    Ensures rule.detection_id == Kibana rule_id.
    """

    with rule_path.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}

    if not isinstance(doc, dict) or "rule" not in doc:
        raise SystemExit(f"Unexpected rule structure in {rule_path}")

    rule_doc = doc.get("rule") or {}
    if not isinstance(rule_doc, dict):
        rule_doc = {}

    # Required: make detection_id match Kibana rule_id
    rule_id = kibana_rule.get("rule_id")
    if not isinstance(rule_id, str) or not rule_id:
        raise SystemExit("Kibana rule JSON does not contain a valid 'rule_id'.")

    rule_doc["detection_id"] = rule_id

    # Title / name
    name = kibana_rule.get("name") or rule_doc.get("title", "")
    if not isinstance(name, str):
        name = str(name)
    rule_doc["title"] = name

    # Description
    description = kibana_rule.get("description") or rule_doc.get("description", "")
    if not isinstance(description, str):
        description = str(description)
    rule_doc["description"] = description

    # Severity and risk score
    severity = kibana_rule.get("severity")
    if isinstance(severity, str) and severity:
        rule_doc["severity"] = severity

    risk_score = kibana_rule.get("risk_score")
    if isinstance(risk_score, int):
        rule_doc["risk_score"] = risk_score

    # Tags
    tags = kibana_rule.get("tags")
    if isinstance(tags, list) and all(isinstance(t, str) for t in tags):
        rule_doc["tags"] = tags

    # Queries
    language = kibana_rule.get("language") or "kql"
    query_body = kibana_rule.get("query") or ""

    if "queries" in rule_doc and isinstance(rule_doc["queries"], list):
        if rule_doc["queries"]:
            q0 = rule_doc["queries"][0]
        else:
            q0 = {}
            rule_doc["queries"].append(q0)
    else:
        rule_doc["queries"] = [{}]
        q0 = rule_doc["queries"][0]

    q0["syntax"] = language
    q0["query"] = query_body

    # Trigger schedule from interval, when available
    interval = kibana_rule.get("interval")
    trigger = rule_doc.get("trigger") or {}
    if not isinstance(trigger, dict):
        trigger = {}
    trigger["schedule"] = interval_to_cron(interval)
    if "condition" not in trigger:
        trigger["condition"] = "results > 0"
    rule_doc["trigger"] = trigger

    # Very simple threat mapping from Elastic 'threat' structure (if present)
    threats = kibana_rule.get("threat") or []
    tactic_techniques = []
    if isinstance(threats, list):
        for t in threats:
            if not isinstance(t, dict):
                continue
            tactic = t.get("tactic") or {}
            techniques = t.get("technique") or []
            tactic_name = tactic.get("name")
            if not tactic_name:
                continue
            entry = {
                "tactic": tactic_name,
                "techniques": [],
            }
            if isinstance(techniques, list):
                for tech in techniques:
                    if not isinstance(tech, dict):
                        continue

                    # Top-level technique
                    tid = tech.get("id")
                    tname = tech.get("name")
                    if tid or tname:
                        entry["techniques"].append(
                            {
                                "id": tid or "",
                                "name": tname or "",
                            }
                        )

                    # Capture subtechniques if present (handles several key shapes,
                    # including the empty-string key used by some Kibana exports).
                    possible_keys = [
                        "subtechniques",
                        "subtechnique",
                        "sub_techniques",
                        "sub-techniques",
                        "",
                    ]
                    sub_lists = []
                    for key in possible_keys:
                        val = tech.get(key)
                        if isinstance(val, list):
                            sub_lists.append(val)
                    # Fallback: scan any list-valued fields for subtechnique-like objects
                    if not sub_lists:
                        for val in tech.values():
                            if isinstance(val, list):
                                sub_lists.append(val)

                    for sub_list in sub_lists:
                        for sub in sub_list:
                            if not isinstance(sub, dict):
                                continue
                            sid = sub.get("id")
                            sname = sub.get("name")
                            if not sid and not sname:
                                continue
                            entry["techniques"].append(
                                {
                                    "id": sid or "",
                                    "name": sname or "",
                                }
                            )

            tactic_techniques.append(entry)

    if tactic_techniques:
        threat_mapping = rule_doc.get("threat_mapping") or {}
        if not isinstance(threat_mapping, dict):
            threat_mapping = {}
        threat_mapping["tactic_techniques"] = tactic_techniques
        rule_doc["threat_mapping"] = threat_mapping

    doc["rule"] = rule_doc

    with rule_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True)

    return doc


def ensure_git_branch(rulebook_root: Path, branch_name: str) -> None:
    """Create and switch to a new git branch in the rulebook repo if possible."""

    def run_git(args: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(rulebook_root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    status = run_git(["rev-parse", "--is-inside-work-tree"])
    if status.returncode != 0:
        # Not a git repo; skip branching
        print(
            f"Warning: {rulebook_root} is not a git repository; "
            "skipping branch creation.",
            file=sys.stderr,
        )
        return

    # Try to create the branch; if it exists, just checkout
    create = run_git(["checkout", "-b", branch_name])
    if create.returncode == 0:
        print(f"Created and switched to branch '{branch_name}' in rulebook repo.")
        return

    # If branch already exists, try to checkout
    checkout = run_git(["checkout", branch_name])
    if checkout.returncode == 0:
        print(f"Switched to existing branch '{branch_name}' in rulebook repo.")
        return

    # If both fail, log but continue
    print(
        f"Warning: failed to create or switch to branch '{branch_name}'.\n"
        f"  create stderr: {create.stderr.strip()}\n"
        f"  checkout stderr: {checkout.stderr.strip()}",
        file=sys.stderr,
    )


def test_git_branch() -> None:
    """Basic smoke test for ensure_git_branch using a temporary git repo."""

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Initialize empty git repo
        init = subprocess.run(
            ["git", "init"],
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if init.returncode != 0:
            raise RuntimeError(f"git init failed: {init.stderr.strip()}")

        branch_name = "import/test-rule"
        ensure_git_branch(repo_root, branch_name)

        # Verify HEAD is on the expected branch
        head = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if head.returncode != 0:
            raise RuntimeError(f"git rev-parse failed: {head.stderr.strip()}")

        current_branch = head.stdout.strip()
        assert (
            current_branch == branch_name
        ), f"Expected branch '{branch_name}', got '{current_branch}'"

    # Also ensure calling with a non-git directory does not raise
    with tempfile.TemporaryDirectory() as tmpdir2:
        non_repo = Path(tmpdir2)
        ensure_git_branch(non_repo, "import/should-not-crash")


def create_rule_with_new_rule(
    rulebook_root: Path, kibana_rule: Dict[str, Any], rule_name: str
) -> Path:
    """
    Use the existing new_rule.py helper in the rulebook repo to create
    a new shared rule file, then return its path.
    """

    new_rule_script = rulebook_root / "scripts" / "new_rule.py"
    if not new_rule_script.exists():
        raise SystemExit(f"new_rule.py not found at {new_rule_script}")

    # Determine platform and title for the new rule
    platform = infer_platform(kibana_rule)
    name = rule_name
    if not isinstance(name, str):
        name = str(name)

    # Call new_rule.py using the same interpreter
    proc = subprocess.run(
        [sys.executable, str(new_rule_script), platform, name],
        cwd=str(rulebook_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(
            "new_rule.py failed:\n"
            f"  stdout: {proc.stdout.strip()}\n"
            f"  stderr: {proc.stderr.strip()}"
        )

    # Parse the created file path from new_rule.py output
    match = re.search(r"File:\s*(.+)", proc.stdout)
    if not match:
        raise SystemExit(
            "Could not determine created rule path from new_rule.py output.\n"
            f"Output was:\n{proc.stdout}"
        )

    path_str = match.group(1).strip()
    rule_path = Path(path_str)
    if not rule_path.is_absolute():
        rule_path = rulebook_root / rule_path

    if not rule_path.exists():
        raise SystemExit(f"Rule file reported by new_rule.py does not exist: {rule_path}")

    return rule_path


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(f"Usage: {argv[0]} <Kibana rule URL> <Branch name> <Rule name>", file=sys.stderr)
        return 1

    kibana_url = argv[1]
    branch_name = argv[2]
    rule_name = argv[3]

    settings = load_settings()
    base_url, rule_id = parse_kibana_rule_url(kibana_url)

    print(f"Kibana base URL: {base_url}")
    print(f"Kibana rule ID: {rule_id}")

    kibana_rule = fetch_rule(base_url, rule_id, settings)

    # Prepare git branch in rulebook repo
    ensure_git_branch(settings.rulebook_base_path, branch_name)

    # Use rulebook's helper script to create the rule file
    rule_path = create_rule_with_new_rule(settings.rulebook_base_path, kibana_rule, rule_name)

    # Populate the created rule file with Kibana details
    doc = populate_rule_file_from_kibana(rule_path, kibana_rule)
    detection_id = doc.get("rule", {}).get("detection_id")

    print("\n=== Import complete ===")
    print(f"Rulebook repo : {settings.rulebook_base_path}")
    print(f"Git branch    : {branch_name}")
    print(f"Rule file     : {rule_path}")
    print(f"detection_id  : {detection_id}")

    return 0




if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

