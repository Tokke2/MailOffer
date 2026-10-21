#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Central versionsinfo för E-postofferten.

En enda sanningskälla för app-versionen. `main.pyw`, Om-dialogen och
GitHub-uppdateraren (`core/github_update.py`) läser alla versionen
härifrån – bumpa BARA här vid ny release.

Releaser på GitHub ska taggas med exakt denna version, t.ex. ``v1.2.0``
för ``__version__ = "1.2.0"`` (uppdateraren jämför taggen mot värdet här).

FIL: core/version.py
"""

from __future__ import annotations

APP_NAME = "E-postofferten"

# App-version (SemVer). Motsvarande GitHub-release-tagg: "v" + __version__.
# (1.0.0 = första publika releasen; äldre 5.x-nummer var interna byggen.)
__version__ = "1.2.0"

# GitHub-repo som autouppdateraren hämtar releaser från ("ägare/repo").
GITHUB_REPO = "Tokke2/MailOffer"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPO}"


def get_version() -> str:
    """Returnera app-versionen, t.ex. ``"1.2.0"``."""
    return __version__


__all__ = ["APP_NAME", "__version__", "GITHUB_REPO", "GITHUB_REPO_URL", "get_version"]
