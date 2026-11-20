
import streamlit as st
import pandas as pd
import plotly.express as px

# CONFIGURATION
st.set_page_config(
    page_title="ECONOMY MONITOR",
    page_icon="📊",
    layout="wide"
)

# STYLE
st.markdown("""
<style>
.stApp {
    background-color: #F5F7FA;
}
h1 {
    color: #142B4A;
    font-weight: 800;
}
h2, h3 {
    color: #142B4A;
}
[data-testid="stMetric"] {
    background-color: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #E4E9F0;
}
</style>
""", unsafe_allow_html=True)

# TITRE
st.title("ECONOMY MONITOR")
st.caption("EURO AREA | ECONOMIC & FINANCIAL DASHBOARD")

st.divider()

# INTRODUCTION
st.markdown("""
Bienvenue sur votre plateforme de suivi économique et financier.

Analysez la conjoncture de la zone euro à travers plusieurs indicateurs
et construisez votre propre baromètre économique.
""")

# INDICATEURS DE DEMONSTRATION
# Ces valeurs sont fictives et servent uniquement à tester l'interface.
indicators = {
    "Croissance du PIB": {"score": 78, "weight": 25},
    "Inflation": {"score": 65, "weight": 20},
    "Chômage": {"score": 72, "weight": 20},
    "Euro Stoxx 50": {"score": 84, "weight": 20},
    "VIX": {"score": 60, "weight": 15}
}

# BARRE LATERALE
st.sidebar.title("PERSONNALISATION")
st.sidebar.caption("Configurez votre baromètre")

selected = {}

for name, data in indicators.items():
    selected[name] = st.sidebar.checkbox(
        name,
        value=True
    )

st.sidebar.divider()
st.sidebar.subheader("Pondération des indicateurs")

weights = {}

for name, data in indicators.items():
    if selected[name]:
        weights[name] = st.sidebar.slider(
            name,
            min_value=0,
            max_value=100,
            value=data["weight"],
            step=5
        )

# CALCUL DU SCORE
active = [
    name for name in indicators
    if selected[name]
]

if active:
    total_weight = sum(weights.values())

    if total_weight > 0:
        score = sum(
            indicators[name]["score"] * weights[name]
            for name in active
        ) / total_weight
    else:
        score = None
else:
    score = None

# AFFICHAGE DU SCORE
st.subheader("Votre baromètre économique")

if score is not None:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("SCORE GLOBAL", f"{score:.1f}/100")

    with col2:
        st.metric("INDICATEURS ACTIFS", f"{len(active)}/5")

    with col3:
        st.metric("PONDÉRATION TOTALE", f"{total_weight}%")

    if score >= 70:
        st.success("Conjoncture favorable selon les indicateurs sélectionnés.")
    elif score >= 50:
        st.warning("Conjoncture intermédiaire : certains indicateurs méritent une attention particulière.")
    else:
        st.error("Conjoncture défavorable selon les indicateurs sélectionnés.")

else:
    st.warning("Sélectionnez au moins un indicateur et attribuez-lui une pondération supérieure à zéro.")

# DETAIL DES INDICATEURS
st.divider()
st.subheader("Analyse des indicateurs")

if active:
    df = pd.DataFrame([
        {
            "Indicateur": name,
            "Score de démonstration": indicators[name]["score"],
            "Pondération choisie": weights[name]
        }
        for name in active
    ])

    st.dataframe(df, use_container_width=True, hide_index=True)

    fig = px.bar(
        df,
        x="Indicateur",
        y="Score de démonstration",
        color="Score de démonstration",
        color_continuous_scale=["#D95F59", "#E8B65B", "#3B9B83"],
        range_y=[0, 100]
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="#142B4A",
        coloraxis_showscale=False
    )

    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("ECONOMY MONITOR | Projet académique de veille économique et financière")

# ==========================================
# TEST DES SOURCES DE DONNEES REELLES
# ==========================================

from data import (
    get_gdp,
    get_inflation,
    get_unemployment,
    get_eurostoxx,
    get_vix
)

@st.cache_data(ttl=3600)
def test_data_sources():
    functions = {
        "Croissance du PIB": get_gdp,
        "Inflation": get_inflation,
        "Chômage": get_unemployment,
        "Euro Stoxx 50": get_eurostoxx,
        "VIX": get_vix
    }

    results = {}

    for name, function in functions.items():
        try:
            df = function()

            if df is not None and not df.empty:
                latest = df.iloc[-1]

                results[name] = {
                    "Statut": "Données récupérées",
                    "Dernière valeur": round(float(latest["Value"]), 2),
                    "Date": latest["Date"].strftime("%d/%m/%Y"),
                    "Nombre d'observations": len(df)
                }
            else:
                results[name] = {
                    "Statut": "Aucune donnée",
                    "Dernière valeur": None,
                    "Date": None,
                    "Nombre d'observations": 0
                }

        except Exception as error:
            results[name] = {
                "Statut": f"Erreur : {str(error)[:100]}",
                "Dernière valeur": None,
                "Date": None,
                "Nombre d'observations": 0
            }

    return pd.DataFrame(results).T


st.divider()
st.subheader("Diagnostic des sources de données")

if st.button("Tester les cinq sources"):
    with st.spinner("Récupération des données en cours..."):
        diagnostic = test_data_sources()

    st.dataframe(diagnostic, use_container_width=True)
