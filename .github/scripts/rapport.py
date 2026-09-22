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

    # Réponses brutes, utiles tant que les noms de champs ne sont pas confirmés.
    print(f"DIAGNOSTIC total ({jour}) : {json.dumps(total)[:500]}")
    print(f"DIAGNOSTIC hits ({jour}) : {json.dumps(pages)[:1500]}")

    hits = pages.get("hits", [])
    pages_vues = sum(ligne.get("count", 0) for ligne in hits)
    clics = sum(
        ligne.get("count", 0)
        for ligne in hits
        if EVENT_TELECHARGEMENT in (ligne.get("path") or "")
    )

    # Selon la version de GoatCounter, le total porte des noms différents.
    visites = 0
    for champ in ("total_unique", "total_unique_utc", "total_utc", "total"):
        valeur = total.get(champ)
        if isinstance(valeur, int) and valeur:
            visites = valeur
            break
    if not visites:
        visites = pages_vues

    return {"visites": visites, "pages_vues": pages_vues or visites, "clics": clics}


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
    return {"total": total, "derniere": derniere}


def bloc_site(titre, jour):
    stats = statistiques_site(jour)
    if not stats:
        return [f"<b>{titre}</b>", "Statistiques indisponibles", ""]
    return [
        f"<b>{titre}</b>",
        f"Visiteurs : {stats['visites']}",
        f"Pages vues : {stats['pages_vues']}",
        f"Clics sur Telecharger : {stats['clics']}",
        "",
    ]


lignes = [f"<b>Equilibre</b> - rapport du {aujourdhui.strftime('%d/%m/%Y')}", ""]
lignes += bloc_site("Site, hier", hier)
lignes += bloc_site("Site, ce jour", aujourdhui)

apk = telechargements_apk()
if apk:
    lignes += ["<b>Application</b>", f"Telechargements APK au total : {apk['total']}"]
    if apk["derniere"]:
        lignes.append(
            f"Derniere version {apk['derniere']['tag']} : {apk['derniere']['compte']} telechargements"
        )
else:
    lignes += ["<b>Application</b>", "Telechargements indisponibles"]

message = "\n".join(lignes)


def envoyer(texte, html=True):
    parametres = {"chat_id": CHAT_ID, "text": texte}
    if html:
        parametres["parse_mode"] = "HTML"
    donnees = urllib.parse.urlencode(parametres).encode()
    urllib.request.urlopen(
        urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=donnees),
        timeout=30,
    )


print(f"Controle : message de {len(message)} caracteres")

try:
    envoyer(message)
    print("Rapport envoye.")
except urllib.error.HTTPError as erreur:
    detail = erreur.read().decode("utf-8", "replace")
    print(f"Telegram a refuse le format HTML ({erreur.code}) : {detail}")
    # Seconde tentative, sans balises de mise en forme.
    envoyer(message.replace("<b>", "").replace("</b>", ""), html=False)
    print("Rapport envoye en texte simple.")
