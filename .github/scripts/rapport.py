"""Rapport Equilibre, envoyé sur Telegram avec les variations depuis le dernier envoi."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

GOAT_SITE = "equilibre-bersi"
EVENT_TELECHARGEMENT = "telechargement-apk"
FICHIER_ETAT = ".github/etat-rapport.json"

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
        return None
    base = f"https://{GOAT_SITE}.goatcounter.com/api/v0"
    entetes = {"Authorization": f"Bearer {GOAT_TOKEN}"}
    periode = urllib.parse.urlencode(
        {"start": f"{jour.isoformat()}T00:00:00Z", "end": f"{jour.isoformat()}T23:59:59Z"}
    )
    try:
        total = get(f"{base}/stats/total?{periode}", entetes)
        pages = get(f"{base}/stats/hits?{periode}", entetes)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as erreur:
        print(f"GoatCounter indisponible : {erreur}")
        return None

    hits = pages.get("hits", [])
    pages_vues = sum(ligne.get("count", 0) for ligne in hits)
    clics = sum(
        ligne.get("count", 0)
        for ligne in hits
        if EVENT_TELECHARGEMENT in (ligne.get("path") or "")
    )
    visites = 0
    for champ in ("total_unique", "total_unique_utc", "total_utc", "total"):
        valeur = total.get(champ)
        if isinstance(valeur, int) and valeur:
            visites = valeur
            break
    return {"visites": visites or pages_vues, "pages_vues": pages_vues, "clics": clics}


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


def variation(actuel, precedent):
    """« +3 » si la valeur a augmenté depuis le dernier rapport, sinon rien."""
    if precedent is None:
        return ""
    ecart = actuel - precedent
    return f"  (+{ecart})" if ecart > 0 else ""


# État du dernier envoi
etat = {}
if os.path.exists(FICHIER_ETAT):
    try:
        with open(FICHIER_ETAT, encoding="utf-8") as fichier:
            etat = json.load(fichier)
    except (OSError, ValueError):
        etat = {}

meme_jour = etat.get("jour") == aujourdhui.isoformat()
site = statistiques_site(aujourdhui)
site_hier = statistiques_site(hier)
apk = telechargements_apk()

# Y a-t-il du nouveau depuis le dernier envoi ?
nouveautes = []
if site:
    if variation(site["visites"], etat.get("visites") if meme_jour else None):
        nouveautes.append("visites")
    if variation(site["clics"], etat.get("clics") if meme_jour else None):
        nouveautes.append("clics")
if apk and variation(apk["total"], etat.get("telechargements")):
    nouveautes.append("telechargements")

heure = datetime.now(timezone(timedelta(hours=1))).strftime("%Hh%M")
titre = "Du nouveau" if nouveautes else "Rapport"
lignes = [f"<b>Equilibre</b> - {titre}, {aujourdhui.strftime('%d/%m/%Y')} a {heure}", ""]

if site:
    lignes += [
        "<b>Site, aujourd hui</b>",
        f"Visiteurs : {site['visites']}{variation(site['visites'], etat.get('visites') if meme_jour else None)}",
        f"Pages vues : {site['pages_vues']}",
        f"Clics sur Telecharger : {site['clics']}{variation(site['clics'], etat.get('clics') if meme_jour else None)}",
        "",
    ]
else:
    lignes += ["<b>Site, aujourd hui</b>", "Statistiques indisponibles", ""]

if site_hier:
    lignes += [
        "<b>Site, hier</b>",
        f"{site_hier['visites']} visiteurs, {site_hier['clics']} clics sur Telecharger",
        "",
    ]

if apk:
    lignes += [
        "<b>Application</b>",
        f"Telechargements APK : {apk['total']}{variation(apk['total'], etat.get('telechargements'))}",
    ]
    if apk["derniere"]:
        lignes.append(f"Derniere version : {apk['derniere']['tag']} ({apk['derniere']['compte']})")
else:
    lignes += ["<b>Application</b>", "Telechargements indisponibles"]

if site and site["visites"] and site["clics"]:
    taux = round(site["clics"] * 100 / site["visites"])
    lignes += ["", f"Taux de telechargement du jour : {taux} %"]

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


try:
    envoyer(message)
    print("Rapport envoye.")
except urllib.error.HTTPError as erreur:
    print(f"Telegram a refuse le HTML ({erreur.code}) : {erreur.read().decode('utf-8', 'replace')}")
    envoyer(message.replace("<b>", "").replace("</b>", ""), html=False)
    print("Rapport envoye en texte simple.")

# Mémorise les chiffres pour le prochain rapport
nouvel_etat = {"jour": aujourdhui.isoformat()}
if site:
    nouvel_etat["visites"] = site["visites"]
    nouvel_etat["clics"] = site["clics"]
if apk:
    nouvel_etat["telechargements"] = apk["total"]

os.makedirs(os.path.dirname(FICHIER_ETAT), exist_ok=True)
with open(FICHIER_ETAT, "w", encoding="utf-8") as fichier:
    json.dump(nouvel_etat, fichier, indent=2)
print("Etat enregistre.")
