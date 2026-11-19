
import streamlit as st

# Configuration de l'application
st.set_page_config(
    page_title="Economy Monitor",
    page_icon="📊",
    layout="wide"
)

# Titre
st.title("ECONOMY MONITOR")
st.caption("Interactive Economic & Financial Monitoring Platform")

st.divider()

# Présentation
st.markdown("""
Bienvenue sur votre plateforme de suivi économique et financier.

Construisez votre propre baromètre en sélectionnant
les indicateurs qui vous intéressent.
""")

# Vérification
st.success("Application initialisée avec succès !")
