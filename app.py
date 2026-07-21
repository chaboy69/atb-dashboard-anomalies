"""
Dashboard de Détection d'Anomalies Bancaires — ATB
Application Streamlit interactive reprenant les 4 pages du tableau de
bord Power BI, avec les mêmes données et la même logique d'interprétation.
"""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# CONFIGURATION GENERALE
# ============================================================
st.set_page_config(
    page_title="Détection d'anomalies bancaires — ATB",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROUGE_ATB = "#A6192E"
BLEU = "#378ADD"
VERT = "#1D9E75"
ORANGE = "#F2A93B"
GRIS = "#7A8B99"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# ============================================================
# CHARGEMENT DES DONNEES (mis en cache pour la performance)
# ============================================================


@st.cache_data
def charger_donnees():
    fichiers_requis = [
        "DETECTION_RESULTS.csv",
        "FEATURE_IMPORTANCE.csv",
        "MODEL_COMPARISON.csv",
        "DATA_MODEL_TRX.csv",
    ]
    manquants = [
        f for f in fichiers_requis if not os.path.exists(os.path.join(DATA_DIR, f))
    ]
    if manquants:
        st.error(
            "**Fichiers de données introuvables.**\n\n"
            f"Dossier de données attendu : `{DATA_DIR}`\n\n"
            f"Fichier(s) manquant(s) : {', '.join(manquants)}\n\n"
            "Vérifie que le dossier `data/` existe bien à la racine du "
            "dépôt GitHub (au même niveau que `app.py`), avec ces "
            "fichiers CSV dedans. Sur GitHub, l'upload par glisser-déposer "
            "aplatit parfois la structure des dossiers : utilise "
            "`data/NOM_DU_FICHIER.csv` comme nom lors de l'upload pour "
            "forcer la création du sous-dossier."
        )
        st.stop()

    detection = pd.read_csv(os.path.join(DATA_DIR, "DETECTION_RESULTS.csv"))
    feature_importance = pd.read_csv(
        os.path.join(DATA_DIR, "FEATURE_IMPORTANCE.csv")
    )
    model_comparison = pd.read_csv(os.path.join(DATA_DIR, "MODEL_COMPARISON.csv"))
    data_model_trx = pd.read_csv(os.path.join(DATA_DIR, "DATA_MODEL_TRX.csv"))

    # Colonnes calculees, equivalentes aux colonnes DAX du modele Power BI
    detection["Statut"] = detection["IF_ANOMALY"].map({1: "Anormal", 0: "Normal"})
    detection["Action_Priorite"] = detection["IF_SCORE"].apply(
        lambda x: "Investiguer" if x > 0.5 else "Surveiller"
    )
    feature_importance["Correlation_Abs"] = feature_importance[
        "Correlation_Score_IF"
    ].abs()

    # Deduplication technique ponctuelle de DATA_MODEL_TRX avant la jointure :
    # certains comptes y apparaissent plusieurs fois (structure multi-produits
    # de la base client), avec des valeurs strictement identiques. Sans cette
    # etape, la jointure produirait des lignes dupliquees et fausserait les
    # analyses par segment.
    data_model_trx = data_model_trx.drop_duplicates(
        subset="ACCOUNT_NO", keep="first"
    )

    # Fusion avec les attributs metier (relation plusieurs-a-un sur ACCOUNT_NO)
    fusion = detection.merge(data_model_trx, on="ACCOUNT_NO", how="left")

    return detection, feature_importance, model_comparison, fusion


detection, feature_importance, model_comparison, fusion = charger_donnees()

# ============================================================
# EN-TETE COMMUN (logos + titre)
# ============================================================


def afficher_entete(titre_page):
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        logo_esprit = os.path.join(ASSETS_DIR, "logo_esprit.png")
        if os.path.exists(logo_esprit):
            st.image(logo_esprit, width=180)
    with col2:
        st.markdown(
            f"<h1 style='text-align:center; color:{ROUGE_ATB}; margin-bottom:0;'>"
            f"{titre_page}</h1>"
            f"<p style='text-align:center; color:#4A5568; margin-top:0;'>"
            f"Détection d'anomalies bancaires — ATB</p>",
            unsafe_allow_html=True,
        )
    with col3:
        logo_atb = os.path.join(ASSETS_DIR, "logo_atb.png")
        if os.path.exists(logo_atb):
            st.image(logo_atb, width=100)
    st.markdown(
        f"<hr style='border: 2px solid {ROUGE_ATB}; margin-top:0;'>",
        unsafe_allow_html=True,
    )


# ============================================================
# NAVIGATION (barre laterale)
# ============================================================
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choisir une page",
    [
        "Vue d'ensemble",
        "Comparaison des modèles",
        "Facteurs explicatifs",
        "Comptes signalés",
    ],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Projet de fin d'études — Détection d'anomalies bancaires\n\n"
    "ESPRIT School of Business × Arab Tunisian Bank"
)

# ============================================================
# PAGE 1 — VUE D'ENSEMBLE
# ============================================================
if page == "Vue d'ensemble":
    afficher_entete("Vue d'ensemble")

    nb_total = len(detection)
    nb_anomalies_if = int(detection["IF_ANOMALY"].sum())
    taux_if = nb_anomalies_if / nb_total
    score_moyen = detection["IF_SCORE"].mean()
    nb_consensus = int(
        (
            detection["IF_ANOMALY"]
            + detection["LOF_ANOMALY"]
            + detection["OCSVM_ANOMALY"]
            + detection["DBSCAN_ANOMALY"]
        )
        .ge(2)
        .sum()
    )
    nb_risque_metier = int(detection["PROXY_RISQUE"].sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Nb Comptes Total", f"{nb_total:,}".replace(",", " "))
    c2.metric("Nb Anomalies IF", f"{nb_anomalies_if:,}".replace(",", " "))
    c3.metric("Taux Anomalie IF", f"{taux_if:.2%}")
    c4.metric("Consensus ≥2 modèles", f"{nb_consensus:,}".replace(",", " "))
    c5.metric("Comptes Risque Métier", f"{nb_risque_metier:,}".replace(",", " "))

    st.markdown("")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.subheader("Répartition des anomalies par modèle")
        counts_modeles = pd.DataFrame(
            {
                "Modèle": ["Isolation Forest", "LOF", "One-Class SVM", "DBSCAN"],
                "Anomalies": [
                    detection["IF_ANOMALY"].sum(),
                    detection["LOF_ANOMALY"].sum(),
                    detection["OCSVM_ANOMALY"].sum(),
                    detection["DBSCAN_ANOMALY"].sum(),
                ],
            }
        )
        fig = px.pie(
            counts_modeles,
            names="Modèle",
            values="Anomalies",
            hole=0.5,
            color_discrete_sequence=[BLEU, VERT, ORANGE, ROUGE_ATB],
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Répartition des anomalies par segment")
        if "PARTYCLASS" in fusion.columns:
            seg = (
                fusion[fusion["IF_ANOMALY"] == 1]
                .groupby("PARTYCLASS")["ACCOUNT_NO"]
                .count()
                .reset_index(name="Anomalies")
            )
            fig = px.pie(
                seg,
                names="PARTYCLASS",
                values="Anomalies",
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Set1,
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig, use_container_width=True)

    with col_c:
        st.subheader("Positionnement des comptes")
        echantillon = detection.sample(
            min(5000, len(detection)), random_state=42
        )
        fig = px.scatter(
            echantillon,
            x="PCA1",
            y="PCA2",
            color="Statut",
            color_discrete_map={"Normal": BLEU, "Anormal": ROUGE_ATB},
            opacity=0.6,
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("")
    st.subheader("Score de risque métier moyen")
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score_moyen,
            gauge={
                "axis": {"range": [0, 1]},
                "bar": {"color": ROUGE_ATB},
                "steps": [
                    {"range": [0, 0.33], "color": "#EAEAEA"},
                    {"range": [0.33, 0.66], "color": "#F5D0D0"},
                    {"range": [0.66, 1], "color": "#E8A5AD"},
                ],
            },
        )
    )
    fig_gauge.update_layout(height=250, margin=dict(t=30, b=10, l=30, r=30))
    st.plotly_chart(fig_gauge, use_container_width=True)

# ============================================================
# PAGE 2 — COMPARAISON DES MODELES
# ============================================================
elif page == "Comparaison des modèles":
    afficher_entete("Comparaison des modèles")

    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.subheader("Précision, rappel et F1-score par modèle")
        melt = model_comparison.melt(
            id_vars=["Modele", "Nb_anomalies"],
            value_vars=["Precision", "Recall", "F1"],
            var_name="Métrique",
            value_name="Valeur",
        )
        fig = px.bar(
            melt,
            x="Modele",
            y="Valeur",
            color="Métrique",
            barmode="group",
            color_discrete_sequence=[BLEU, ROUGE_ATB, VERT],
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Tableau comparatif")
        style = model_comparison.style.background_gradient(
            subset=["F1"], cmap="RdYlGn"
        ).format({"Precision": "{:.2f}", "Recall": "{:.2f}", "F1": "{:.2f}"})
        st.dataframe(style, use_container_width=True, hide_index=True)

        meilleur = model_comparison.loc[model_comparison["F1"].idxmax()]
        st.markdown(
            f"""
            <div style='background-color:#FFF5F5; border-left:5px solid {ROUGE_ATB};
                        padding:15px; border-radius:8px; margin-top:15px;'>
            <b>L'Isolation Forest est retenu comme modèle principal
            (F1 = {meilleur['F1']:.3f}).</b> Les trois autres méthodes sont
            fournies à titre comparatif.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.metric("Modèle retenu", meilleur["Modele"])

# ============================================================
# PAGE 3 — FACTEURS EXPLICATIFS
# ============================================================
elif page == "Facteurs explicatifs":
    afficher_entete("Facteurs explicatifs")

    col_a, col_b = st.columns([3, 2])

    top15 = feature_importance.reindex(
        feature_importance["Correlation_Abs"].sort_values(ascending=False).index
    ).head(15)
    top15 = top15.sort_values("Correlation_Score_IF")

    with col_a:
        st.subheader("Variables les plus associées au score d'anomalie")
        fig = px.bar(
            top15,
            x="Correlation_Score_IF",
            y="Feature",
            orientation="h",
            color="Correlation_Score_IF",
            color_continuous_scale=["#1D5FA8", "#EAEAEA", ROUGE_ATB],
            range_color=[-0.5, 0.5],
        )
        fig.update_layout(height=500, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Tableau détaillé (42 variables)")
        st.dataframe(
            feature_importance[["Feature", "Correlation_Score_IF"]]
            .sort_values("Correlation_Score_IF", ascending=False)
            .style.format({"Correlation_Score_IF": "{:.2f}"}),
            use_container_width=True,
            hide_index=True,
            height=350,
        )

        st.markdown(
            f"""
            <div style='background-color:#F5F6F8; border-left:5px solid {ROUGE_ATB};
                        padding:15px; border-radius:8px; margin-top:15px;'>
            Les variables liées au volume et à la volatilité des transactions
            (nombre de transactions, montant maximal, écart-type des
            montants) sont les plus déterminantes du score d'anomalie.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ============================================================
# PAGE 4 — COMPTES SIGNALES
# ============================================================
elif page == "Comptes signalés":
    afficher_entete("Comptes signalés")

    col_filtre, col_table = st.columns([1, 4])

    with col_filtre:
        st.subheader("Filtres")
        segments_dispo = (
            sorted(fusion["PARTYCLASS"].dropna().unique())
            if "PARTYCLASS" in fusion.columns
            else []
        )
        segments_choisis = st.multiselect(
            "Segment (PARTYCLASS)", segments_dispo, default=segments_dispo
        )
        action_choisie = st.multiselect(
            "Action prioritaire",
            ["Investiguer", "Surveiller"],
            default=["Investiguer", "Surveiller"],
        )
        score_min, score_max = st.slider(
            "Score de risque métier", 0, 3, (0, 3)
        )

        st.markdown("---")
        st.metric("Score IF Moyen", f"{detection['IF_SCORE'].mean():.3f}")

    with col_table:
        st.subheader("Comptes triés par score d'anomalie décroissant")

        df_filtre = fusion.copy()
        if segments_dispo:
            df_filtre = df_filtre[df_filtre["PARTYCLASS"].isin(segments_choisis)]
        df_filtre = df_filtre[df_filtre["Action_Priorite"].isin(action_choisie)]
        df_filtre = df_filtre[
            df_filtre["SCORE_RISQUE_METIER"].between(score_min, score_max)
        ]
        df_filtre = df_filtre.sort_values("IF_SCORE", ascending=False)

        colonnes_affichees = [
            "ACCOUNT_NO",
            "PARTYCLASS",
            "IF_SCORE",
            "SCORE_RISQUE_METIER",
            "Action_Priorite",
            "IF_ANOMALY",
            "LOF_ANOMALY",
            "OCSVM_ANOMALY",
            "DBSCAN_ANOMALY",
        ]
        colonnes_affichees = [c for c in colonnes_affichees if c in df_filtre.columns]

        def couleur_action(val):
            if val == "Investiguer":
                return "background-color: #F8D0D5"
            if val == "Surveiller":
                return "background-color: #FCE8C8"
            return ""

        st.caption(f"{len(df_filtre):,} comptes correspondant aux filtres".replace(",", " "))
        st.dataframe(
            df_filtre[colonnes_affichees]
            .head(500)
            .style.applymap(couleur_action, subset=["Action_Priorite"])
            .format({"IF_SCORE": "{:.2f}"}),
            use_container_width=True,
            hide_index=True,
            height=500,
        )
