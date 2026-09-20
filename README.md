# Equilibre — site de téléchargement

Site statique d'une page présentant l'application **Equilibre** (comptabilité personnelle hors ligne
pour Android) et proposant le téléchargement de l'APK.

## Contenu

```
index.html              page d'accueil et bouton de téléchargement
confidentialite.html    politique de confidentialité
assets/                 logo, favicon, image de partage, captures d'écran
```

## Mise en ligne avec GitHub Pages

1. Créez un dépôt, par exemple `equilibre`, et poussez ces fichiers à la racine.
2. Dans le dépôt : **Settings → Pages**.
3. *Source* : **Deploy from a branch**. *Branch* : `main`, dossier `/ (root)`. Enregistrez.
4. Après une ou deux minutes, le site est en ligne sur `https://PSEUDO.github.io/equilibre/`.

## Publier l'APK

L'APK ne se met **pas** dans le dépôt : il se publie dans une *Release*.

1. Onglet **Releases → Draft a new release**.
2. *Tag* : `v1.0.0`. *Title* : `Equilibre 1.0.0`.
3. Glissez le fichier `equilibre.apk` dans la zone **Attach binaries**.
4. **Publish release**.

Le lien permanent vers la dernière version devient :

```
https://github.com/PSEUDO/DEPOT/releases/latest/download/equilibre.apk
```

## À personnaliser avant publication

- Remplacer `PSEUDO/DEPOT` dans `index.html` (bouton, lien « Toutes les versions », pied de page, script).
- Remplacer `contact@example.com` par votre adresse, dans les deux pages.
- Ajouter vos captures d'écran : `assets/ecran-1.png` à `assets/ecran-4.png`, au format portrait.

## Conseils

- Nommez toujours le fichier `equilibre.apk`, pour que le lien `latest/download` reste valable.
- Signez chaque version avec **la même clé**, sinon les mises à jour échoueront.
- `flutter build apk --split-per-abi` réduit fortement la taille ; publiez alors la variante `arm64-v8a`.
