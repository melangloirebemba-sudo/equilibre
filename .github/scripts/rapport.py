"""Rapport quotidien Equilibre, envoyé sur Telegram."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

GOAT_SITE = "equilibre-bersi"
EVENT_TELECHARGEMENT = "telechargement-apk"

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GOAT_TOKEN = os.environ.get("GOATCOUNTER_TOKEN", "")
REPO = os.environ.get("GITHUB_REPO", "melangloirebemba-sudo/equilibre")

aujourdhui = date.today()
hier = aujourdhui - timedelta(days=1)


def get(url, headers=None):
    requete = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        return json.load(reponse)


def statistiques_site(jour):
    """Visites et clics sur le bouton de téléchargement, pour un jour donné."""
    if not GOAT_TOKEN:
        print("Diagnostic : le secret GOATCOUNTER_TOKEN est vide.")
        return None
    base = f"https://{GOAT_SITE}.goatcounter.com/api/v0"
    entetes = {"Authorization": f"Bearer {GOAT_TOKEN}"}
    periode = urllib.parse.urlencode(
        {"start": f"{jour.isoformat()}T00:00:00Z", "end": f"{jour.isoformat()}T23:59:59Z"}
    )
    try:
        total = get(f"{base}/stats/total?{periode}", entetes)
        pages = get(f"{base}/stats/hits?{periode}", entetes)
    except urllib.error.HTTPError as erreur:
        print(f"Diagnostic : {erreur.code} : {erreur.read().decode('utf-8', 'replace')[:300]}")
        return None
    except (urllib.error.URLError, ValueError) as erreur:
        print(f"Diagnostic : appel GoatCounter impossible ({erreur})")
        return None

    # Réponses brutes, pour ajuster les noms de champs si besoin.
    print(f"DIAGNOSTIC total ({jour}) : {json.dumps(total)[:500]}")
    print(f"DIAGNOSTIC hits ({jour}) : {json.dumps(pages)[:1500]}")

    clics = 0
    for ligne in pages.get("hits", []):
        if EVENT_TELECHARGEMENT in (ligne.get("path") or ""):
            clics += ligne.get("count", 0)
    return {
        "visites": total.get("total_unique", 0),
        "pages_vues": total.get("total", 0),
        "clics": clics,
    }


def telechargements_apk():
    """Téléchargements par release, via l'API GitHub."""
    try:
        releases = get(
            f"https://api.github.com/repos/{REPO}/releases",
            {"Accept": "application/vnd.github+json"},
        )
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError):
        return None

    total = 0
    derniere = None
    for release in releases:
        compte = sum(
            asset.get("download_count", 0)
            for asset in release.get("assets", [])
            if asset.get("name", "").lower().endswith(".apk")
        )
        total += compte
        if derniere is None:
            derniere = {"tag": release.get("tag_name", "?"), "compte": compte}
    return
