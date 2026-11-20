
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

from scoring import calculate_scores, calculate_global_score


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
    st.caption("Les données sont mises en cache pendant 24 heures. Leur fréquence de publication dépend de chaque source.")


# ==========================================
# RECUPERATION
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
        "description": "Variation trimestrielle annualisée de référence"
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
        "description": "Indice de volatilité anticipée des marchés américains"
    }
}


# ==========================================
# BARRE LATERALE
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

st.divider()
st.subheader("Votre baromètre économique")

if global_score is not None:

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("SCORE GLOBAL", f"{global_score:.1f}/100")

    with col2:
        st.metric("INDICATEURS ACTIFS", f"{len(active_scores)}/5")

    with col3:
        total_weight = sum(
            weight for name, weight in weights.items()
            if name in active_scores
        )
        st.metric("POIDS SAISIS", f"{total_weight}%")

    if global_score >= 70:
        st.success("Conjoncture favorable selon les indicateurs sélectionnés.")
    elif global_score >= 50:
        st.warning("Conjoncture intermédiaire : certains indicateurs méritent une attention particulière.")
    else:
        st.error("Conjoncture défavorable selon les indicateurs sélectionnés.")

else:
    st.warning(
        "Sélectionnez au moins un indicateur et attribuez-lui "
        "une pondération supérieure à zéro."
    )


# ==========================================
# DETAIL DES INDICATEURS
# ==========================================

st.divider()
st.subheader("Analyse des indicateurs")

cards = st.columns(5)

for i, (name, info) in enumerate(indicators.items()):

    df = data.get(info["key"])

    with cards[i]:

        st.markdown(f"**{name}**")

        if df is not None and not df.empty:

            latest = df.iloc[-1]
            value = float(latest["Value"])
            date = latest["Date"].strftime("%d/%m/%Y")

            if name in ["Croissance du PIB", "Inflation", "Chômage"]:
                formatted = f"{value:.2f}%"
            else:
                formatted = f"{value:,.2f}"

            st.metric("Dernière valeur", formatted)

            if name in scores:
                st.metric("Score /100", f"{scores[name]:.1f}")

            st.caption(f"Observation : {date}")

        else:
            st.warning("Donnée indisponible")


# ==========================================
# GRAPHIQUES HISTORIQUES
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

    fig = px.line(
        chart_data,
        x="Date",
        y="Value",
        title=f"Évolution de {chosen}",
        markers=False
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="#142B4A",
        xaxis_title="Date",
        yaxis_title="Valeur",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)


# ==========================================
# METHODOLOGIE ET SOURCES
# ==========================================

st.divider()

with st.expander("Comprendre la méthodologie de notation"):

    st.markdown("""
    Chaque indicateur est transformé en un score compris entre 0 et 100.

    - **PIB :** score croissant selon la croissance économique.
    - **Inflation :** score maximal autour de 2 %.
    - **Chômage :** score décroissant lorsque le chômage augmente.
    - **Euro Stoxx 50 :** position relative du dernier niveau dans son historique.
    - **VIX :** score décroissant lorsque la volatilité augmente.

    Le score global correspond à la moyenne pondérée des scores
    des indicateurs sélectionnés.

    Les pondérations sont automatiquement normalisées lors du calcul.
    """)

with st.expander("Sources des données"):

    st.markdown("""
    - PIB : Eurostat — `namq_10_gdp`
    - Inflation : Eurostat — `prc_hicp_manr` et `prc_hicp_minr`
    - Chômage : Eurostat — `une_rt_m`
    - Euro Stoxx 50 : Yahoo Finance — `^STOXX50E`
    - VIX : Yahoo Finance — `^VIX`
    """)

st.caption(
    "ECONOMY MONITOR | Projet académique de veille économique et financière"
)
