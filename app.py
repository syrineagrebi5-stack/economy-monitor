
import streamlit as st
import pandas as pd
import plotly.express as px

from data import (
    get_gdp,
    get_inflation,
    get_unemployment,
    get_eurostoxx,
    get_vix
)

from scoring import (
    calculate_scores,
    calculate_global_score,
    score_gdp,
    score_inflation,
    score_unemployment,
    score_eurostoxx,
    score_vix
)


# ==========================================
# CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="ECONOMY MONITOR",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #F5F7FA;
}

h1, h2, h3 {
    color: #142B4A;
}

[data-testid="stMetric"] {
    background-color: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #E4E9F0;
}

[data-testid="stSidebar"] {
    background-color: #EDF1F6;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# CHARGEMENT DES DONNEES
# ==========================================

@st.cache_data(ttl=86400)
def load_all_data():
    return {
        "gdp": get_gdp(),
        "inflation": get_inflation(),
        "unemployment": get_unemployment(),
        "eurostoxx": get_eurostoxx(),
        "vix": get_vix()
    }


# ==========================================
# TITRE
# ==========================================

st.title("ECONOMY MONITOR")
st.caption("EURO AREA | ECONOMIC & FINANCIAL DASHBOARD")

st.markdown("""
Suivez l'évolution de la conjoncture économique et financière
de la zone euro à travers cinq indicateurs clés.

Personnalisez votre baromètre en sélectionnant les indicateurs
et en ajustant leur importance dans le calcul du score global.
""")

st.divider()


# ==========================================
# ACTUALISATION
# ==========================================

col_refresh, col_info = st.columns([1, 3])

with col_refresh:
    if st.button("Actualiser les données"):
        st.cache_data.clear()
        st.rerun()

with col_info:
    st.caption(
        "Les données sont mises en cache pendant 24 heures. "
        "Leur fréquence de publication dépend de chaque source."
    )


# ==========================================
# RECUPERATION DES DONNEES
# ==========================================

with st.spinner("Chargement des données économiques et financières..."):
    try:
        data = load_all_data()
        scores = calculate_scores(data)
        loading_error = None

    except Exception as error:
        data = {}
        scores = {}
        loading_error = str(error)

if loading_error:
    st.error(f"Erreur lors du chargement : {loading_error}")
    st.stop()

# ==========================================
# CONFIGURATION DES INDICATEURS
# ==========================================

indicators = {
    "Croissance du PIB": {
        "key": "gdp",
        "weight": 25,
        "unit": "%",
        "description": "Variation trimestrielle du PIB, corrigée des effets saisonniers"
    },
    "Inflation": {
        "key": "inflation",
        "weight": 20,
        "unit": "%",
        "description": "Variation annuelle de l'indice des prix"
    },
    "Chômage": {
        "key": "unemployment",
        "weight": 20,
        "unit": "%",
        "description": "Part des actifs au chômage"
    },
    "Euro Stoxx 50": {
        "key": "eurostoxx",
        "weight": 20,
        "unit": "pts",
        "description": "Indice boursier des grandes entreprises de la zone euro"
    },
    "VIX": {
        "key": "vix",
        "weight": 15,
        "unit": "pts",
        "label": "VIX – Risque financier international",
        "description": "Volatilité anticipée du marché américain, révélatrice de l'aversion au risque"
    }
}


# ==========================================
# BARRE LATERALE : PERSONNALISATION
# ==========================================

st.sidebar.title("PERSONNALISATION")
st.sidebar.caption("Construisez votre propre baromètre")

selected = {}
weights = {}

for name, info in indicators.items():

    available = name in scores

    selected[name] = st.sidebar.checkbox(
        name,
        value=available,
        disabled=not available,
        help="Indicateur indisponible si aucune donnée n'a été récupérée."
    )

st.sidebar.divider()
st.sidebar.subheader("Pondération")

for name, info in indicators.items():

    if selected[name]:

        weights[name] = st.sidebar.slider(
            name,
            min_value=0,
            max_value=100,
            value=info["weight"],
            step=5
        )


# ==========================================
# CALCUL DU SCORE GLOBAL
# ==========================================

active_scores = {
    name: scores[name]
    for name in indicators
    if selected.get(name, False) and name in scores
}

global_score = calculate_global_score(
    active_scores,
    weights
)

total_active_weight = sum(
    weight for name, weight in weights.items()
    if name in active_scores
)

normalized_weights = {
    name: round(weight / total_active_weight * 100, 1)
    for name, weight in weights.items()
    if name in active_scores and weight > 0 and total_active_weight > 0
}

# ==========================================
# EXPORT DES DONNEES ET DES SCORES EN CSV
# ==========================================

st.divider()
st.subheader("Export des données et des scores")

export_rows = []

indicator_keys = {
    "Croissance du PIB": "gdp",
    "Inflation": "inflation",
    "Chômage": "unemployment",
    "Euro Stoxx 50": "eurostoxx",
    "VIX": "vix"
}

for name, key in indicator_keys.items():

    df = data.get(key)

    if df is not None and not df.empty:

        clean_export = df.copy()

        clean_export["Value"] = pd.to_numeric(
            clean_export["Value"],
            errors="coerce"
        )

        clean_export["Date"] = pd.to_datetime(
            clean_export["Date"],
            errors="coerce"
        )

        clean_export = clean_export.dropna(
            subset=["Value", "Date"]
        ).sort_values("Date")

        if not clean_export.empty:

            latest = clean_export.iloc[-1]

            export_rows.append({
                "Indicateur": name,
                "Date": latest["Date"].strftime("%Y-%m-%d"),
                "Valeur brute": float(latest["Value"]),
                "Score normalisé": active_scores.get(name),
                "Poids (%)": normalized_weights.get(name),
                "Score global": global_score
            })

if export_rows:

    export_df = pd.DataFrame(export_rows)

    csv_file = export_df.to_csv(
        index=False,
        sep=";",
        encoding="utf-8-sig"
    )

    st.download_button(
        label="📥 Télécharger les données et les scores (CSV)",
        data=csv_file,
        file_name="economy_monitor_complete.csv",
        mime="text/csv"
    )

else:

    st.warning("Aucune donnée disponible pour l'export.")


# ==========================================
# AFFICHAGE DU SCORE GLOBAL
# ==========================================

st.divider()
st.subheader("Votre baromètre économique")

if global_score is not None:

    if global_score >= 70:
        appreciation = "Situation favorable"
        couleur = "#16A34A"
        message = "Conjoncture favorable selon les indicateurs sélectionnés."

    elif global_score >= 40:
        appreciation = "Situation modérée"
        couleur = "#D97706"
        message = "Certains indicateurs méritent une attention particulière."

    else:
        appreciation = "Situation dégradée"
        couleur = "#DC2626"
        message = "Conjoncture défavorable selon les indicateurs sélectionnés."

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:

        st.markdown(
            f"""
            <div style="
                background-color: white;
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                border: 1px solid #E2E8F0;
                min-height: 150px;
            ">
                <div style="font-size: 15px; color: #64748B;">
                    SCORE GLOBAL
                </div>
                <div style="font-size: 52px; font-weight: bold; color: {couleur};">
                    {global_score:.1f}<span style="font-size: 22px;">/100</span>
                </div>
                <div style="font-size: 18px; font-weight: 600; color: {couleur};">
                    {appreciation}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.metric("INDICATEURS ACTIFS", f"{len(active_scores)}/5")

    with col3:
        st.metric("POIDS SAISIS", f"{total_active_weight}%")

    st.info(message)

else:

    st.warning(
        "Sélectionnez au moins un indicateur et attribuez-lui "
        "une pondération supérieure à zéro."
    )


# ==========================================
# AVERTISSEMENT METHODOLOGIQUE
# ==========================================

st.warning("""
⚠️ **À propos du score global**

Le score global constitue un indicateur synthétique de
l'environnement macroéconomique et financier. Il dépend
des indicateurs retenus, des seuils de normalisation
et des pondérations définies.

Il ne constitue ni une prévision de marché, ni un conseil
en investissement, ni un signal automatique d'achat ou de vente.
""")


# ==========================================
# DETAIL DES INDICATEURS
# ==========================================


st.divider()

if global_score is not None and active_scores:

    st.markdown("### Interprétation économique du baromètre")

    if global_score >= 70:
        interpretation = (
            "La situation économique et financière apparaît favorable. "
            "Les indicateurs sélectionnés traduisent globalement "
            "un environnement positif."
        )

    elif global_score >= 40:
        interpretation = (
            "La situation économique et financière apparaît modérée. "
            "Certains indicateurs présentent des fragilités "
            "qui méritent une attention particulière."
        )

    else:
        interpretation = (
            "La situation économique et financière apparaît dégradée. "
            "Les indicateurs signalent un environnement défavorable."
        )

    st.write(interpretation)

    macro_names = [
        "Croissance du PIB",
        "Inflation",
        "Chômage"
    ]

    macro_scores = {
        name: active_scores[name]
        for name in macro_names
        if name in active_scores
    }

    if macro_scores:

        weakest = sorted(
            macro_scores.items(),
            key=lambda item: item[1]
        )[:2]

        st.markdown("**Points de vigilance macroéconomiques :**")

        for name, score in weakest:
            st.write(f"- {name} : {score:.1f}/100")

    st.markdown("**Signaux des marchés financiers :**")

    if "Euro Stoxx 50" in active_scores:

        score_euro = active_scores["Euro Stoxx 50"]

        if score_euro >= 70:
            st.write("- Euro Stoxx 50 : dynamique boursière favorable.")

        elif score_euro >= 40:
            st.write("- Euro Stoxx 50 : dynamique boursière modérée.")

        else:
            st.write("- Euro Stoxx 50 : dynamique boursière défavorable.")

    if "VIX" in active_scores:

        vix_score = active_scores["VIX"]

        if vix_score >= 70:
            st.write(
                "- VIX : volatilité anticipée relativement faible, "
                "signal d'un environnement de marché plus serein."
            )

        elif vix_score >= 40:
            st.write(
                "- VIX : volatilité modérée, traduisant une certaine "
                "incertitude sur les marchés."
            )

        else:
            st.write(
                "- VIX : volatilité élevée, signalant une forte "
                "nervosité des marchés."
            )



# ==========================================
# ANALYSE DES INDICATEURS
# ==========================================

st.subheader("Analyse des indicateurs")

if normalized_weights:

    st.markdown("#### Contribution des indicateurs au score global")

    contribution_df = pd.DataFrame([
        {
            "Indicateur": name,
            "Score individuel": round(active_scores[name], 1),
            "Pondération effective": f"{weight:.1f}%",
            "Contribution au score": round(
                active_scores[name] * weight / 100, 2
            )
        }
        for name, weight in normalized_weights.items()
        if name in active_scores
    ])

    st.dataframe(
        contribution_df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "La contribution correspond au score individuel multiplié "
        "par la pondération effective de chaque indicateur."
    )

    st.markdown("#### Poids des indicateurs dans le score global")

    contribution_chart = px.bar(
        contribution_df,
        x="Indicateur",
        y="Contribution au score",
        text="Contribution au score",
        title="Contribution de chaque indicateur"
    )

    contribution_chart.update_traces(
        marker_color="#2563EB",
        textposition="outside",
        texttemplate="%{text:.2f}"
    )

    contribution_chart.update_layout(
        showlegend=False,
        yaxis_title="Points apportés au score global",
        xaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(
            showgrid=True,
            gridcolor="#E2E8F0",
            rangemode="tozero"
        )
    )

    st.plotly_chart(
        contribution_chart,
        use_container_width=True
    )


# ==========================================
# TENDANCE DES INDICATEURS
# ==========================================

def get_indicator_trend(name, df):

    if df is None or len(df) < 2:
        return None

    history = df.copy()

    history["Value"] = pd.to_numeric(
        history["Value"],
        errors="coerce"
    )

    history = (
        history.dropna(subset=["Value", "Date"])
        .sort_values("Date")
    )

    if len(history) < 2:
        return None

    previous = float(history.iloc[-2]["Value"])
    current = float(history.iloc[-1]["Value"])

    variation = current - previous

    if variation == 0:
        status = "Stable"

    elif name == "Inflation":

        previous_distance = abs(previous - 2)
        current_distance = abs(current - 2)

        if current_distance < previous_distance:
            status = "Amélioration"

        elif current_distance > previous_distance:
            status = "Dégradation"

        else:
            status = "Stable"

    elif name in ["Croissance du PIB", "Euro Stoxx 50"]:

        status = (
            "Amélioration" if variation > 0
            else "Dégradation"
        )

    else:

        status = (
            "Amélioration" if variation < 0
            else "Dégradation"
        )

    return variation, status


# ==========================================
# CALCUL DE L'HISTORIQUE DU SCORE GLOBAL
# ==========================================

def calculate_historical_global_score(data, selected, weights):

    all_dates = []

    keys = [
        "gdp",
        "inflation",
        "unemployment",
        "eurostoxx",
        "vix"
    ]

    # Récupération des dates
    for key in keys:

        df = data.get(key)

        if df is not None and not df.empty:

            dates = pd.to_datetime(
                df["Date"],
                errors="coerce"
            ).dropna()

            all_dates.extend(dates.tolist())

    if not all_dates:
        return None

    dates = sorted(set(all_dates))

    historical_scores = []

    for date in dates:

        historical_data = {}

        # Données disponibles à la date considérée
        for key in keys:

            df = data.get(key)

            if df is None or df.empty:
                historical_data[key] = None
                continue

            history = df.copy()

            history["Date"] = pd.to_datetime(
                history["Date"],
                errors="coerce"
            )

            history["Value"] = pd.to_numeric(
                history["Value"],
                errors="coerce"
            )

            history = history.dropna(
                subset=["Date", "Value"]
            )

            available = history[
                history["Date"] <= date
            ].sort_values("Date")

            if available.empty:
                historical_data[key] = None

            else:
                historical_data[key] = available.copy()

        scores = {}

        # PIB
        if selected.get("Croissance du PIB"):

            history = historical_data["gdp"]

            if history is not None and not history.empty:

                value = history["Value"].iloc[-1]

                scores["Croissance du PIB"] = score_gdp(
                    float(value)
                )

        # Inflation
        if selected.get("Inflation"):

            history = historical_data["inflation"]

            if history is not None and not history.empty:

                value = history["Value"].iloc[-1]

                scores["Inflation"] = score_inflation(
                    float(value)
                )

        # Chômage
        if selected.get("Chômage"):

            history = historical_data["unemployment"]

            if history is not None and not history.empty:

                value = history["Value"].iloc[-1]

                scores["Chômage"] = score_unemployment(
                    float(value)
                )

        # Euro Stoxx 50
        if selected.get("Euro Stoxx 50"):

            history = historical_data["eurostoxx"]

            if history is not None and not history.empty:

                euro_score = score_eurostoxx(history)

                if euro_score is not None:
                    scores["Euro Stoxx 50"] = euro_score

        # VIX
        if selected.get("VIX"):

            history = historical_data["vix"]

            if history is not None and not history.empty:

                vix_values = pd.to_numeric(
                    history["Value"],
                    errors="coerce"
                ).dropna()

                if not vix_values.empty:

                    vix_value = float(
                        vix_values.iloc[-1]
                    )

                    scores["VIX"] = score_vix(vix_value)

        # Calcul du score global historique
        historical_score = calculate_global_score(
            scores,
            weights
        )

        if historical_score is not None:

            historical_scores.append({
                "Date": date,
                "Score global": historical_score
            })

    if not historical_scores:
        return None

    result = pd.DataFrame(historical_scores)

    result["Date"] = pd.to_datetime(
        result["Date"]
    )

    result = result.sort_values("Date")

    return result


# ==========================================
# CARTES DES CINQ INDICATEURS
# ==========================================

cards = st.columns(5)

for i, (name, info) in enumerate(indicators.items()):

    df = data.get(info["key"])

    with cards[i]:

        st.markdown(
            f"""
            <div style="
                background-color: white;
                border: 1px solid #E4E9F0;
                border-radius: 12px;
                padding: 15px;
                min-height: 115px;
            ">
                <div style="
                    color: #142B4A;
                    font-size: 17px;
                    font-weight: 700;
                    min-height: 45px;
                ">
                    {name}
                </div>
                <div style="
                    color: #64748B;
                    font-size: 12px;
                    height: 75px;
                ">
                    {info["description"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if df is not None and not df.empty:

            clean_df = df.copy()

            clean_df["Value"] = pd.to_numeric(
                clean_df["Value"],
                errors="coerce"
            )

            clean_df = clean_df.dropna(
                subset=["Value", "Date"]
            ).sort_values("Date")

            if not clean_df.empty:

                latest = clean_df.iloc[-1]
                value = float(latest["Value"])

                if name == "Croissance du PIB":

                    quarter = (
                        (latest["Date"].month - 1) // 3 + 1
                    )

                    date = (
                        f"T{quarter} {latest['Date'].year}"
                    )

                else:

                    date = latest["Date"].strftime(
                        "%d/%m/%Y"
                    )

                if name in [
                    "Croissance du PIB",
                    "Inflation",
                    "Chômage"
                ]:

                    formatted = f"{value:.2f}%"

                else:

                    formatted = f"{value:,.2f}"

                st.metric(
                    "Dernière valeur",
                    formatted
                )

                if name in scores:

                    st.metric(
                        "Score /100",
                        f"{scores[name]:.1f}"
                    )

                trend = get_indicator_trend(
                    name,
                    clean_df
                )

                if trend is not None:

                    variation, status = trend

                    if name in [
                        "Croissance du PIB",
                        "Inflation",
                        "Chômage"
                    ]:

                        variation_text = (
                            f"{variation:+.2f} point(s)"
                        )

                    else:

                        variation_text = (
                            f"{variation:+.2f}"
                        )

                    if status == "Amélioration":

                        st.success(
                            f"↑ {variation_text} — Amélioration"
                        )

                    elif status == "Dégradation":

                        st.error(
                            f"↓ {variation_text} — Dégradation"
                        )

                    else:

                        st.info(
                            f"→ Stable ({variation_text})"
                        )

                st.caption(
                    f"Observation : {date}"
                )

            else:

                st.warning("Donnée indisponible")

        else:

            st.warning("Donnée indisponible")


# ==========================================
# HISTORIQUE DU SCORE GLOBAL
# ==========================================

st.divider()

st.subheader(
    "Évolution historique du score global"
)

if global_score is not None:

    try:

        historical_data = calculate_historical_global_score(
            data,
            selected,
            weights
        )

        if (
            historical_data is not None
            and not historical_data.empty
        ):

            historical_fig = px.line(
                historical_data,
                x="Date",
                y="Score global",
                title="Évolution du baromètre économique"
            )

            historical_fig.update_traces(
                line=dict(
                    color="#2563EB",
                    width=3
                ),
                hovertemplate=(
                    "<b>Date :</b> %{x|%d/%m/%Y}<br>"
                    "<b>Score :</b> %{y:.1f}/100"
                    "<extra></extra>"
                )
            )

            historical_fig.add_hline(
                y=70,
                line_dash="dash",
                line_color="#16A34A",
                annotation_text="Situation favorable"
            )

            historical_fig.add_hline(
                y=40,
                line_dash="dash",
                line_color="#D97706",
                annotation_text="Seuil de situation modérée"
            )

            historical_fig.update_layout(
                yaxis=dict(
                    title="Score global /100",
                    range=[0, 100]
                ),
                xaxis_title="Date",
                plot_bgcolor="white",
                paper_bgcolor="white",
                hovermode="x unified",
                height=450
            )

            st.plotly_chart(
                historical_fig,
                use_container_width=True
            )

        else:

            st.info(
                "Les données historiques sont insuffisantes "
                "pour calculer un score global."
            )

    except Exception as error:
        st.error("Erreur dans le calcul historique")
        st.exception(error)
else:

    st.info(
        "Activez au moins un indicateur avec une pondération "
        "positive pour afficher l'historique."
    )


# ==========================================
# GRAPHIQUES HISTORIQUES INDIVIDUELS
# ==========================================

st.divider()

st.subheader("Évolution historique")

available_names = [
    name for name, info in indicators.items()
    if data.get(info["key"]) is not None
    and not data[info["key"]].empty
]

if available_names:

    chosen = st.selectbox(
        "Choisissez un indicateur",
        available_names
    )

    chosen_key = indicators[chosen]["key"]

    chart_data = data[chosen_key].copy()

    chart_data["Date"] = pd.to_datetime(
        chart_data["Date"],
        errors="coerce"
    )

    chart_data["Value"] = pd.to_numeric(
        chart_data["Value"],
        errors="coerce"
    )

    chart_data = chart_data.dropna(
        subset=["Date", "Value"]
    )

    chart_data["Année"] = chart_data["Date"].dt.year

    available_years = sorted(
        chart_data["Année"].unique().tolist(),
        reverse=True
    )

    selected_year = st.selectbox(
        "Choisissez une année",
        ["Toutes les années"] + available_years
    )

    if selected_year != "Toutes les années":

        chart_data = chart_data[
            chart_data["Année"] == selected_year
        ]

    chart_data = chart_data.sort_values("Date")

    if chosen in [
        "Croissance du PIB",
        "Inflation",
        "Chômage"
    ]:

        y_title = "Valeur (%)"

        hover_template = (
            "<b>Date :</b> %{x|%d/%m/%Y}<br>"
            "<b>Valeur :</b> %{y:.2f}%"
            "<extra></extra>"
        )

    else:

        y_title = "Valeur de l'indice"

        hover_template = (
            "<b>Date :</b> %{x|%d/%m/%Y}<br>"
            "<b>Valeur :</b> %{y:,.2f}"
            "<extra></extra>"
        )

    fig = px.line(
        chart_data,
        x="Date",
        y="Value",
        title=f"Évolution de {chosen}"
    )

    fig.update_traces(
        line=dict(
            color="#2563EB",
            width=3
        ),
        fill="tozeroy",
        fillcolor="rgba(37, 99, 235, 0.08)",
        hovertemplate=hover_template
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(
            family="Arial",
            color="#142B4A",
            size=12
        ),
        title=dict(
            font=dict(
                size=18,
                color="#142B4A"
            ),
            x=0
        ),
        xaxis=dict(
            title="Date",
            showgrid=False,
            showline=True,
            linecolor="#CBD5E1",
            tickfont=dict(color="#64748B")
        ),
        yaxis=dict(
            title=y_title,
            showgrid=True,
            gridcolor="#E2E8F0",
            zeroline=True,
            zerolinecolor="#CBD5E1",
            tickfont=dict(color="#64748B")
        ),
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        ),
        height=420
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.warning(
        "Aucune série historique disponible."
    )


# ==========================================
# METHODOLOGIE ET SOURCES
# ==========================================

st.divider()

with st.expander("Comprendre la méthodologie de notation"):

    st.markdown("""
    Chaque indicateur est transformé en un score compris entre 0 et 100.
    Un score élevé traduit une situation plus favorable.

    **Méthodes de normalisation :**

    - **PIB :** normalisation linéaire entre -2 % (score 0) et +4 % (score 100).
    - **Inflation :** score maximal de 100 autour de la cible de 2 %. Le score diminue à mesure que l'écart à cette cible augmente.
    - **Chômage :** normalisation inversée entre 3 % (score 100) et 12 % (score 0).
    - **Euro Stoxx 50 :** performance boursière sur 12 mois. Une performance de -20 % donne un score de 0, 0 % un score de 50 et +20 % ou plus un score de 100.
    - **VIX :** normalisation inversée entre 10 (score 100) et 40 (score 0). Une volatilité élevée traduit une aversion au risque plus importante.

    **Construction du score global :**

    Le score global correspond à la moyenne pondérée des scores
    des indicateurs sélectionnés.

    Les pondérations sont automatiquement normalisées afin que
    leur somme soit égale à 100 %, même lorsque certains indicateurs
    sont désactivés.

    Les seuils et pondérations constituent des conventions
    méthodologiques retenues pour construire ce baromètre.
    Le score ne constitue pas une prévision officielle de la conjoncture.
    """)

with st.expander("Sources des données"):

    st.markdown("""
    **Eurostat — Commission européenne**

    Base de données statistiques officielle de l'Union européenne.

    - PIB : `namq_10_gdp`
    - Inflation : `prc_hicp_manr` et `prc_hicp_minr`
    - Chômage : `une_rt_m`

    Site : https://ec.europa.eu/eurostat

    **Yahoo Finance**

    Données historiques des marchés financiers.

    - Euro Stoxx 50 : `^STOXX50E`
    - VIX : `^VIX`

    Site : https://finance.yahoo.com

    **Méthode de collecte**

    Les données sont récupérées automatiquement avec Python,
    à l'aide de requêtes HTTP vers Eurostat et de la bibliothèque
    yfinance pour les données financières.

    Les données sont mises en cache pendant 24 heures.
    """)
