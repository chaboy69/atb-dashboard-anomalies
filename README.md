# Dashboard de Détection d'Anomalies Bancaires — ATB

Application Streamlit reprenant les 4 pages du tableau de bord Power BI
(Vue d'ensemble, Comparaison des modèles, Facteurs explicatifs, Comptes
signalés), à partir des mêmes fichiers de résultats issus du notebook de
détection d'anomalies.

## Structure du projet

```
streamlit_app/
├── app.py                  # Application principale
├── requirements.txt         # Dépendances Python
├── data/
│   ├── DETECTION_RESULTS.csv
│   ├── FEATURE_IMPORTANCE.csv
│   ├── MODEL_COMPARISON.csv
│   └── DATA_MODEL_TRX.csv   # Colonnes essentielles uniquement (allégé)
└── assets/
    ├── logo_esprit.png
    └── logo_atb.png
```

## Exécution en local

1. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
2. Lancer l'application depuis le dossier `streamlit_app/` :
   ```bash
   streamlit run app.py
   ```
3. L'application s'ouvre automatiquement dans le navigateur à l'adresse
   `http://localhost:8501`.

## Déploiement sur le web (Streamlit Community Cloud — gratuit)

1. Créer un dépôt GitHub contenant l'intégralité de ce dossier
   (`app.py`, `requirements.txt`, `data/`, `assets/`)
2. Se connecter sur [share.streamlit.io](https://share.streamlit.io) avec
   un compte GitHub
3. Cliquer sur **New app**, sélectionner le dépôt et le fichier `app.py`
4. Déployer — l'application est accessible via une URL publique
   (`https://<nom-app>.streamlit.app`)

**Remarque** : le fichier `DATA_MODEL_TRX.csv` a été réduit aux 9 colonnes
strictement nécessaires (identifiant de compte, segment, statut, devise,
solde, salaire) afin de rester léger pour un déploiement en ligne. Le
fichier original complet reste disponible séparément si besoin d'enrichir
l'application.

## Mise à jour des données

Pour rafraîchir le dashboard avec de nouveaux résultats, il suffit de
remplacer les fichiers CSV dans le dossier `data/` par les nouvelles
exportations du notebook, en conservant exactement les mêmes noms de
fichiers et de colonnes. Aucune modification du code n'est nécessaire.

## Note technique

Une déduplication ponctuelle est appliquée en interne sur
`DATA_MODEL_TRX.csv` avant la jointure avec les résultats de détection,
afin d'éviter une multiplication artificielle des lignes liée à la
structure multi-produits de la base client source (un même compte peut
apparaître plusieurs fois dans le fichier brut). Cette déduplication ne
concerne que cette jointure spécifique et n'affecte pas les résultats des
modèles de détection eux-mêmes, calculés en amont sur 26 929 comptes.
