"""
Dividenden-Tracker — Startseite (Dashboard)
"""
import streamlit as st

from datenbank import init_db, lade_positionen
from marktdaten import hole_aktien_daten, hole_wechselkurs, in_euro
from sidebar import render_sidebar

# ==========================================================
# SETUP
# ==========================================================

st.set_page_config(
    page_title="Dividenden-Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    h1 {
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 1.5rem;
    }
    [data-testid="stMetric"] {
        background-color: rgba(46, 134, 171, 0.08);
        padding: 15px 20px;
        border-radius: 10px;
        border-left: 4px solid #2E86AB;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar auf jeder Seite gleich
render_sidebar()

# ==========================================================
# DASHBOARD
# ==========================================================

st.title("📈 Dividenden-Tracker")
st.markdown("*Deine persönliche Dividenden-Übersicht — ehrlich und transparent.*")

positionen = lade_positionen()

if positionen.empty:
    st.info(
        "👋 **Willkommen!** Du hast noch keine Positionen angelegt. "
        "Wechsle zur Seite **Portfolio** in der linken Navigation, um deine erste Aktie hinzuzufügen."
    )
    st.stop()

# Kennzahlen berechnen
gesamt_wert_eur = 0.0
gesamt_dividende_brutto_eur = 0.0
anzahl_positionen = 0

for _, position in positionen.iterrows():
    daten = hole_aktien_daten(position["ticker"])
    if daten is None or daten["kurs"] == 0:
        continue
    anzahl_positionen += 1
    wert = position["stueckzahl"] * daten["kurs"]
    dividende = position["stueckzahl"] * daten["dividende_jahr"]
    wert_eur = in_euro(wert, daten["waehrung"])
    div_eur = in_euro(dividende, daten["waehrung"])
    if wert_eur:
        gesamt_wert_eur += wert_eur
    if div_eur:
        gesamt_dividende_brutto_eur += div_eur

st.subheader("📊 Überblick")
k1, k2, k3, k4 = st.columns(4)
k1.metric("💼 Positionen", f"{anzahl_positionen}")
k2.metric("💰 Portfoliowert", f"{gesamt_wert_eur:,.0f} €")
k3.metric("📅 Dividende/Jahr (brutto)", f"{gesamt_dividende_brutto_eur:,.0f} €")
k4.metric("📆 Dividende/Monat (Ø)", f"{gesamt_dividende_brutto_eur/12:,.0f} €")

st.divider()

usd_eur = hole_wechselkurs("USD", "EUR")
if usd_eur:
    st.caption(f"💱 Aktueller Wechselkurs: 1 USD = {usd_eur:.4f} EUR")

st.subheader("🧭 Wohin jetzt?")
n1, n2 = st.columns(2)

with n1:
    with st.container(border=True):
        st.markdown("### 💼 Portfolio")
        st.write("Positionen anlegen, Sparraten einstellen, Reinvest-Modus konfigurieren.")
        if st.button("Zum Portfolio →", key="nav_portfolio", use_container_width=True):
            st.switch_page("pages/1_💼_Portfolio.py")

with n2:
    with st.container(border=True):
        st.markdown("### 🔮 Simulation")
        st.write("Schau dir an, wie sich dein Portfolio über die nächsten Jahre entwickelt.")
        if st.button("Zur Simulation →", key="nav_simulation", use_container_width=True):
            st.switch_page("pages/2_🔮_Simulation.py")

st.caption(
    "ℹ️ *Diese App ist keine Anlage- oder Steuerberatung. "
    "Alle Simulationen basieren auf aktuellen Marktdaten, die sich jederzeit ändern können.*"
)