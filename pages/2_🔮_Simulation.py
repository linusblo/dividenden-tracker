"""
Simulation und Zukunftsprojektion.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta
from streamlit_calendar import calendar

from config import PAUSCHBETRAG_DEFAULT, FARBE_PRIMAER, FARBE_SEKUNDAER
from datenbank import init_db, lade_positionen
from marktdaten import hole_aktien_daten, in_euro
from dividenden import projiziere_dividenden
from simulation import simuliere_portfolio
from sidebar import render_sidebar

st.set_page_config(page_title="Simulation", page_icon="🔮", layout="wide")
init_db()
render_sidebar()

# Einstellungen aus Session State
pauschbetrag = st.session_state.get("pauschbetrag", PAUSCHBETRAG_DEFAULT)
simulations_jahre = st.session_state.get("sim_jahre", 10)

st.title("🔮 Simulation")
st.markdown(
    f"*Projektion über **{simulations_jahre} Jahre** mit aktuellen Kursen und Dividenden. "
    f"Einstellungen änderst du in der Sidebar links.*"
)

positionen = lade_positionen()
if positionen.empty:
    st.info("📭 Keine Positionen vorhanden. Wechsle zur Seite **💼 Portfolio** und lege zuerst welche an.")
    st.stop()

# ==========================================================
# KALENDER (nächste 12 Monate)
# ==========================================================

st.header("📅 Dividenden-Kalender")
st.caption("Alle erwarteten Dividendenzahlungen der nächsten 12 Monate als Kalenderansicht.")

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
    # Feste Farbe pro Ticker
    farbpalette = [
        "#2E86AB", "#06A77D", "#F18F01", "#C73E1D",
        "#6C5B7B", "#355C7D", "#F67280", "#2A9D8F"
    ]
    ticker_farben = {}
    for eintrag in alle_zahlungen:
        ticker = eintrag["ticker"]
        if ticker not in ticker_farben:
            ticker_farben[ticker] = farbpalette[len(ticker_farben) % len(farbpalette)]
    
    # Events für den Kalender bauen
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
        "height": 600,
    }
    
    calendar(events=events, options=kalender_optionen, key="dividenden_kalender")
    
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
# LANGZEIT-SIMULATION
# ==========================================================

st.header(f"📈 Langzeit-Simulation ({simulations_jahre} Jahre)")

with st.spinner("Simulation läuft..."):
    events_df, end_status = simuliere_portfolio(positionen, simulations_jahre, pauschbetrag)

if events_df.empty:
    st.warning("Keine Simulations-Events erzeugt.")
    st.stop()

# Kennzahlen
end_wert_eur = 0.0
for status in end_status.values():
    wert = status["bestand"] * status["kurs"]
    wert_eur = in_euro(wert, status["waehrung"])
    if wert_eur:
        end_wert_eur += wert_eur

dividenden_events = events_df[events_df["Typ"].str.startswith("Dividende")]
sparraten_events = events_df[events_df["Typ"] == "Sparrate"]
summe_div_netto = dividenden_events["Netto_EUR"].sum() if not dividenden_events.empty else 0
summe_steuern = 0.0
if not dividenden_events.empty:
    summe_steuern = dividenden_events["Quellensteuer_EUR"].sum() + dividenden_events["Deutsche_Steuer_EUR"].sum()
summe_einzahlungen = sparraten_events["Betrag_EUR"].sum() if not sparraten_events.empty else 0

st.subheader(f"🎯 Ergebnis nach {simulations_jahre} Jahren")
k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Depotwert", f"{end_wert_eur:,.0f} €")
k2.metric("💶 Eingezahlt", f"{summe_einzahlungen:,.0f} €")
k3.metric("🤑 Dividenden netto", f"{summe_div_netto:,.0f} €")
k4.metric("🧾 Steuern", f"{summe_steuern:,.0f} €")

# Chart: Bestand pro Position
st.subheader("📊 Aktien-Bestand pro Position")
bestand_df = events_df.copy().sort_values("Datum")
bestand_df["Monat"] = pd.to_datetime(bestand_df["Datum"]).dt.to_period("M").dt.to_timestamp()
bestand_monat = bestand_df.groupby(["Monat", "Ticker"], as_index=False)["Bestand_danach"].last()
fig_bestand = px.line(
    bestand_monat, x="Monat", y="Bestand_danach", color="Ticker",
    labels={"Bestand_danach": "Aktien-Bestand", "Monat": ""},
)
fig_bestand.update_layout(height=400)
st.plotly_chart(fig_bestand, use_container_width=True)

# Chart: Einzahlungen vs. Dividenden
st.subheader("💸 Eingezahltes Kapital vs. Dividenden (kumuliert)")
monat_df = events_df.copy()
monat_df["Monat"] = pd.to_datetime(monat_df["Datum"]).dt.to_period("M").dt.to_timestamp()

fig_kumuliert = go.Figure()
sparraten_df = monat_df[monat_df["Typ"] == "Sparrate"]
if not sparraten_df.empty:
    einzahlungen_monat = sparraten_df.groupby("Monat")["Betrag_EUR"].sum().cumsum()
    fig_kumuliert.add_trace(go.Scatter(
        x=einzahlungen_monat.index, y=einzahlungen_monat.values,
        name="Eingezahltes Kapital", fill="tozeroy", mode="lines",
        line=dict(color=FARBE_PRIMAER)
    ))
dividenden_df = monat_df[monat_df["Typ"].str.startswith("Dividende")]
if not dividenden_df.empty:
    dividenden_monat = dividenden_df.groupby("Monat")["Netto_EUR"].sum().cumsum()
    fig_kumuliert.add_trace(go.Scatter(
        x=dividenden_monat.index, y=dividenden_monat.values,
        name="Netto-Dividenden (kumuliert)", mode="lines",
        line=dict(color=FARBE_SEKUNDAER, width=3)
    ))
fig_kumuliert.update_layout(height=400, yaxis_title="€")
st.plotly_chart(fig_kumuliert, use_container_width=True)

# Chart: Monatliche Dividenden
st.subheader("📅 Monatliche Dividenden (netto)")
if not dividenden_df.empty:
    div_pro_monat = dividenden_df.groupby("Monat")["Netto_EUR"].sum().reset_index()
    fig_div = px.bar(
        div_pro_monat, x="Monat", y="Netto_EUR",
        labels={"Netto_EUR": "Netto-Dividende (€)", "Monat": ""},
        color_discrete_sequence=[FARBE_SEKUNDAER],
    )
    fig_div.update_layout(height=400)
    st.plotly_chart(fig_div, use_container_width=True)

# Alle Events
with st.expander("🔍 Alle Simulations-Events"):
    events_anzeige = events_df.copy()
    events_anzeige["Datum"] = pd.to_datetime(events_anzeige["Datum"]).dt.strftime("%d.%m.%Y")
    st.dataframe(events_anzeige, use_container_width=True, hide_index=True)