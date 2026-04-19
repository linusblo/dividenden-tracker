"""
Dividenden-Tracker — Startseite (Dashboard) mit Kalender und Portfolio-Übersicht
"""
import streamlit as st
import pandas as pd
from streamlit_calendar import calendar

from datenbank import init_db, lade_positionen
from marktdaten import hole_aktien_daten, hole_wechselkurs, in_euro
from dividenden import projiziere_dividenden, erkenne_rhythmus, rhythmus_text, hole_dividenden_historie
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

render_sidebar()

# ==========================================================
# DASHBOARD
# ==========================================================

st.title("📈 Dividenden-Tracker")
st.markdown("*Deine persönliche Dividenden-Übersicht — ehrlich und transparent.*")

positionen = lade_positionen()

if positionen.empty:
    st.info(
        "👋 **Willkommen!** Es sind noch keine Positionen angelegt. "
        "Wechsle zur Seite **💼 Portfolio** in der linken Navigation, um die erste Aktie hinzuzufügen."
    )
    if st.button("Zum Portfolio →", type="primary"):
        st.switch_page("pages/1_💼_Portfolio.py")
    st.stop()

# ---------- Kennzahlen ----------
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
k3.metric("📅 Dividende/Jahr", f"{gesamt_dividende_brutto_eur:,.0f} €")
k4.metric("📆 Dividende/Monat (Ø)", f"{gesamt_dividende_brutto_eur/12:,.0f} €")

usd_eur = hole_wechselkurs("USD", "EUR")
if usd_eur:
    st.caption(f"💱 Aktueller Wechselkurs: 1 USD = {usd_eur:.4f} EUR")

st.divider()

# ==========================================================
# KALENDER
# ==========================================================

st.subheader("📅 Dividenden-Kalender")
st.caption("Alle erwarteten Dividendenzahlungen der nächsten 12 Monate.")

alle_zahlungen = []
for _, position in positionen.iterrows():
    daten = hole_aktien_daten(position["ticker"])
    if daten is None:
        continue
    projektionen = projiziere_dividenden(position["ticker"], position["stueckzahl"], monate_voraus=12)
    for p in projektionen:
        betrag_eur = in_euro(p["gesamt"], daten["waehrung"])
        if betrag_eur is None:
            continue
        alle_zahlungen.append({
            "datum": p["datum"],
            "ticker": position["ticker"],
            "name": daten["name"],
            "betrag": betrag_eur,
        })

if alle_zahlungen:
    farbpalette = [
        "#2E86AB", "#06A77D", "#F18F01", "#C73E1D",
        "#6C5B7B", "#355C7D", "#F67280", "#2A9D8F"
    ]
    ticker_farben = {}
    for eintrag in alle_zahlungen:
        ticker = eintrag["ticker"]
        if ticker not in ticker_farben:
            ticker_farben[ticker] = farbpalette[len(ticker_farben) % len(farbpalette)]
    
    events = []
    for eintrag in alle_zahlungen:
        events.append({
            "title": eintrag["ticker"],
            "start": eintrag["datum"].strftime("%Y-%m-%d"),
            "end": eintrag["datum"].strftime("%Y-%m-%d"),
            "backgroundColor": ticker_farben[eintrag["ticker"]],
            "borderColor": ticker_farben[eintrag["ticker"]],
        })
    
    kalender_optionen = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,listMonth",
        },
        "initialView": "dayGridMonth",
        "locale": "de",
        "buttonText": {
            "today": "Heute",
            "month": "Monat",
            "list": "Liste",
        },
        "height": 550,
    }
    
    calendar(events=events, options=kalender_optionen, key="dashboard_kalender")
    
    # Legende
    st.markdown("**Legende:**")
    legende_spalten = st.columns(min(len(ticker_farben), 6))
    for i, (ticker, farbe) in enumerate(ticker_farben.items()):
        with legende_spalten[i % len(legende_spalten)]:
            st.markdown(
                f"<span style='background-color:{farbe};color:white;padding:3px 10px;border-radius:5px;font-size:0.9em;'>{ticker}</span>",
                unsafe_allow_html=True
            )
else:
    st.info("Keine Dividenden-Projektionen verfügbar.")

st.divider()

# ==========================================================
# AKTIEN-LISTE
# ==========================================================

st.subheader("🗂️ Aktien im Depot")

liste_daten = []
for _, position in positionen.iterrows():
    daten = hole_aktien_daten(position["ticker"])
    if daten is None or daten["kurs"] == 0:
        continue
    historie = hole_dividenden_historie(position["ticker"])
    rhythmus = erkenne_rhythmus(historie) if historie is not None else None
    rhythmus_str = rhythmus_text(rhythmus) if rhythmus else "unbekannt"
    
    wert = position["stueckzahl"] * daten["kurs"]
    dividende = position["stueckzahl"] * daten["dividende_jahr"]
    wert_eur = in_euro(wert, daten["waehrung"]) or 0
    div_eur = in_euro(dividende, daten["waehrung"]) or 0
    
    liste_daten.append({
        "Ticker": position["ticker"],
        "Name": daten["name"],
        "Stückzahl": round(position["stueckzahl"], 4),
        "Wert (€)": round(wert_eur, 2),
        "Div./Jahr (€)": round(div_eur, 2),
        "Rhythmus": rhythmus_str,
    })

if liste_daten:
    df_liste = pd.DataFrame(liste_daten)
    st.dataframe(df_liste, use_container_width=True, hide_index=True)

st.divider()

# ==========================================================
# NAVIGATION
# ==========================================================

st.subheader("🧭 Wohin weiter?")
n1, n2 = st.columns(2)

with n1:
    with st.container(border=True):
        st.markdown("### 💼 Portfolio bearbeiten")
        st.write("Positionen hinzufügen, löschen, Sparraten einstellen.")
        if st.button("Zum Portfolio →", key="nav_portfolio", use_container_width=True):
            st.switch_page("pages/1_💼_Portfolio.py")

with n2:
    with st.container(border=True):
        st.markdown("### 🔮 Simulation")
        st.write("Langzeit-Projektion über mehrere Jahre mit Reinvestment und Steuern.")
        if st.button("Zur Simulation →", key="nav_simulation", use_container_width=True):
            st.switch_page("pages/2_🔮_Simulation.py")

st.caption(
    "ℹ️ *Diese App ist keine Anlage- oder Steuerberatung. "
    "Alle Simulationen basieren auf aktuellen Marktdaten, die sich jederzeit ändern können.*"
)