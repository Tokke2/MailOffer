#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synkronisera GitHub Release-tagg + markera releasen som Latest vid kodförändring.

HÅRD REGEL i E-postofferten:
  Appens inbyggda uppdaterare (`core/github_update.py`) hämtar alltid
  `/releases/latest` över HTTPS och jämför `BUILD_ID` samt varenda appfils
  SHA-256 mot den taggade releasens commit/zipball.
  Därför MÅSTE varje verifierad kodförändring på arbetsbranchen:
    1. Flytta release-taggen (`v{__version__}`, t.ex. `v1.0.0`) till aktuell commit-SHA.
    2. Uppdatera (eller skapa) motsvarande GitHub Release med aktuell `<!-- build: ... -->`,
       `draft=False`, `prerelease=False` och `make_latest="true"`.
    3. Aldrig publicera från `main` eller `master`.

Körs automatiskt i GitHub Actions (`sync-latest-release` efter gröna tester)
och kan även köras manuellt lokalt (`python tools/sync_latest_release.py`).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.version import APP_NAME, BUILD_ID, __version__

DEFAULT_REPO = "Tokke2/MailOffer"
FORBIDDEN_BRANCHES = frozenset({"main", "master", "head"})

ApiCaller = Callable[[str, str, Optional[Dict[str, Any]]], Any]


def update_release_body_build_marker(
    existing_body: str, build_id: str, note: str = ""
) -> str:
    """Uppdatera `<!-- build: ... -->` och lägg vid behov till nytt BUILD-avsnitt."""
    bid = str(build_id or "").strip()
    body = str(existing_body or "")
    marker = f"<!-- build: {bid} -->"
    if re.search(r"<!--\s*build:\s*[^>]+-->", body, flags=re.IGNORECASE):
        body = re.sub(
            r"<!--\s*build:\s*[^>]+-->",
            marker,
            body,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        body = f"{marker}\n\n{body}".strip()

    clean_note = str(note or "").strip()
    heading = f"## BUILD{bid}"
    if clean_note and heading not in body:
        body = f"{body.rstrip()}\n\n{heading}\n{clean_note}\n"
    return body


def build_release_patch_payload(
    *,
    tag: str,
    target_commitish: str,
    name: str,
    body: str,
) -> Dict[str, Any]:
    """Bygg payload som garanterar skarp release markerad som `Latest`."""
    branch_check = str(target_commitish or "").strip().lower()
    if branch_check in FORBIDDEN_BRANCHES:
        raise ValueError(
            f"Otillåten branch för release: {target_commitish!r} (main/master är förbjudna)."
        )
    return {
        "tag_name": tag,
        "target_commitish": target_commitish,
        "name": name,
        "body": body,
        "draft": False,
        "prerelease": False,
        "make_latest": "true",
    }


def _http_github_api(
    token: str, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None
) -> Any:
    url = f"https://api.github.com/{endpoint.lstrip('/')}"
    data = (
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if payload is not None
        else None
    )
    req = urllib.request.Request(url=url, data=data, method=method.upper())
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "MailOffer-ReleaseSync/1.0")
    if data is not None:
        req.add_header("Content-Type", "application/json; charset=utf-8")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw) if raw.strip() else {}


def _gh_cli_api(
    method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None
) -> Any:
    cmd = ["gh", "api", "-X", method.upper(), endpoint.lstrip("/")]
    stdin_text: Optional[str] = None
    if payload is not None:
        cmd.extend(["--input", "-"])
        stdin_text = json.dumps(payload, ensure_ascii=False)
    proc = subprocess.run(
        cmd,
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"gh api {method} {endpoint} misslyckades ({proc.returncode}): {proc.stderr.strip()}"
        )
    out = proc.stdout.strip()
    return json.loads(out) if out else {}


def make_default_api_caller() -> ApiCaller:
    token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if token:
        return lambda method, endpoint, payload=None: _http_github_api(
            token, method, endpoint, payload
        )
    return _gh_cli_api


def sync_release(
    *,
    repo: str,
    commit_sha: str,
    branch: str,
    version: str = __version__,
    build_id: str = BUILD_ID,
    note: str = "",
    api: Optional[ApiCaller] = None,
) -> Tuple[str, int]:
    """Flytta versionstaggen till `commit_sha` och uppdatera releasen som `Latest`."""
    sha = str(commit_sha or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError(f"Ogiltig commit-SHA: {commit_sha!r}")
    clean_branch = str(branch or "").strip()
    if clean_branch.lower() in FORBIDDEN_BRANCHES:
        raise ValueError(f"Release får aldrig synkas från {clean_branch!r}")

    caller = api or make_default_api_caller()
    tag = f"v{str(version).lstrip('v')}"

    # 1. Flytta eller skapa git-taggen refs/tags/v{version} -> exakt commit_sha
    try:
        caller(
            "PATCH",
            f"repos/{repo}/git/refs/tags/{tag}",
            {"sha": sha, "force": True},
        )
    except Exception:
        caller(
            "POST",
            f"repos/{repo}/git/refs",
            {"ref": f"refs/tags/{tag}", "sha": sha},
        )

    # 2. Hitta befintlig release för taggen (eller skapa ny)
    existing: Optional[Dict[str, Any]] = None
    releases = caller("GET", f"repos/{repo}/releases?per_page=30", None)
    if isinstance(releases, list):
        for rel in releases:
            if isinstance(rel, dict) and rel.get("tag_name") == tag:
                existing = rel
                break

    release_name = (
        str(existing.get("name") or "").strip()
        if existing
        else f"{APP_NAME} {version}"
    ) or f"{APP_NAME} {version}"
    old_body = str(existing.get("body") or "") if existing else ""
    updated_body = update_release_body_build_marker(old_body, build_id, note=note)
    target = clean_branch or sha
    payload = build_release_patch_payload(
        tag=tag,
        target_commitish=target,
        name=release_name,
        body=updated_body,
    )

    if existing and existing.get("id"):
        rel_id = int(existing["id"])
        updated = caller("PATCH", f"repos/{repo}/releases/{rel_id}", payload)
    else:
        updated = caller("POST", f"repos/{repo}/releases", payload)
        rel_id = int(updated["id"])

    # 3. Verifiera att /releases/latest nu pekar på denna release
    latest = caller("GET", f"repos/{repo}/releases/latest", None)
    if not isinstance(latest, dict) or latest.get("tag_name") != tag:
        raise RuntimeError(
            f"Verifiering misslyckades: /releases/latest är {latest!r}, förväntade tagg {tag!r}"
        )
    if latest.get("draft") or latest.get("prerelease"):
        raise RuntimeError("Releasen får varken vara draft eller prerelease.")
    return tag, rel_id


def _detect_git_head_and_branch() -> Tuple[str, str]:
    sha = (os.environ.get("GITHUB_SHA") or "").strip()
    if not sha:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True
        ).strip()
    branch = (os.environ.get("GITHUB_REF_NAME") or "").strip()
    if not branch:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(ROOT), text=True
        ).strip()
    return sha, branch


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO))
    parser.add_argument("--sha", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)

    det_sha, det_branch = _detect_git_head_and_branch()
    sha = args.sha or det_sha
    branch = args.branch or det_branch
    tag, rel_id = sync_release(
        repo=args.repo,
        commit_sha=sha,
        branch=branch,
        note=args.note,
    )
    print(
        f"Synkade GitHub Release {tag} (id={rel_id}, make_latest=true) -> {sha[:12]} ({branch}), BUILD_ID={BUILD_ID}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
