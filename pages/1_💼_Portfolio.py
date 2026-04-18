"""
Portfolio-Verwaltung: Positionen anlegen, bearbeiten, löschen.
"""
import streamlit as st

from config import INTERVALL_OPTIONEN
from datenbank import (
    init_db, lade_positionen, speichere_position,
    aktualisiere_sparrate, aktualisiere_reinvest, loesche_position
)
from marktdaten import hole_aktien_daten, hole_dividenden_historie, hole_wechselkurs, in_euro
from dividenden import erkenne_rhythmus, rhythmus_text
from sidebar import render_sidebar

st.set_page_config(page_title="Portfolio", page_icon="💼", layout="wide")
init_db()
render_sidebar()

st.title("💼 Portfolio")
st.markdown("*Verwalte hier deine Positionen und die Einstellungen pro Aktie.*")

# Wechselkurs-Info
usd_eur = hole_wechselkurs("USD", "EUR")
if usd_eur:
    st.caption(f"💱 Aktueller Wechselkurs: 1 USD = {usd_eur:.4f} EUR")

# ---------- Neue Position ----------
with st.container(border=True):
    st.subheader("➕ Neue Position hinzufügen")
    
    with st.form("neue_position", clear_on_submit=True):
        spalte1, spalte2, spalte3 = st.columns([2, 1, 1])
        with spalte1:
            ticker_input = st.text_input("Ticker-Symbol", placeholder="z.B. ARCC, MAIN, O")
        with spalte2:
            stueckzahl_input = st.number_input("Stückzahl", min_value=0.0, step=1.0)
        with spalte3:
            st.write("")
            st.write("")
            abschicken = st.form_submit_button("Hinzufügen", use_container_width=True, type="primary")
        
        if abschicken:
            if ticker_input and stueckzahl_input > 0:
                daten = hole_aktien_daten(ticker_input.upper())
                if daten and daten["kurs"] > 0:
                    speichere_position(ticker_input, stueckzahl_input)
                    st.success(f"✅ {daten['name']} ({ticker_input.upper()}) hinzugefügt!")
                    st.rerun()
                else:
                    st.error(f"❌ Ticker '{ticker_input}' nicht gefunden.")
            else:
                st.warning("⚠️ Bitte Ticker und Stückzahl angeben.")

# ---------- Bestehende Positionen ----------
st.subheader("📋 Meine Positionen")

positionen = lade_positionen()

if positionen.empty:
    st.info("Noch keine Positionen angelegt. Füge oben deine erste Aktie hinzu!")
    st.stop()

for _, position in positionen.iterrows():
    daten = hole_aktien_daten(position["ticker"])
    if daten is None or daten["kurs"] == 0:
        with st.container(border=True):
            st.warning(f"⚠️ Keine Daten für {position['ticker']} verfügbar")
        continue
    
    wert = position["stueckzahl"] * daten["kurs"]
    dividende_jahr = position["stueckzahl"] * daten["dividende_jahr"]
    kurs_eur = in_euro(daten["kurs"], daten["waehrung"])
    wert_eur = in_euro(wert, daten["waehrung"])
    dividende_eur = in_euro(dividende_jahr, daten["waehrung"])
    
    historie = hole_dividenden_historie(position["ticker"])
    rhythmus = erkenne_rhythmus(historie)
    rhythmus_str = rhythmus_text(rhythmus) if rhythmus else "unbekannt"
    reinvest_an = bool(position["reinvest_dividende"])
    reinvest_symbol = "🔁" if reinvest_an else "💵"
    reinvest_text = "reinvestiert" if reinvest_an else "Cash"
    
    with st.container(border=True):
        spalten = st.columns([2, 1, 1, 1, 1, 0.5])
        spalten[0].markdown(
            f"**{daten['name']}**  \n"
            f"`{position['ticker']}` · {daten['waehrung']} · {rhythmus_str} · {reinvest_symbol} {reinvest_text}"
        )
        spalten[1].metric("Stückzahl", f"{position['stueckzahl']:.4f}")
        spalten[2].metric("Kurs", f"{kurs_eur:.2f} €" if kurs_eur else "n/a")
        spalten[3].metric("Wert", f"{wert_eur:.2f} €" if wert_eur else "n/a")
        spalten[4].metric("Div./Jahr", f"{dividende_eur:.2f} €" if dividende_eur else "n/a")
        
        if spalten[5].button("🗑️", key=f"del_{position['id']}", help="Position löschen"):
            loesche_position(position["id"])
            st.rerun()
        
        with st.expander("⚙️ Einstellungen"):
            st.markdown("**💰 Sparrate**")
            sp1, sp2, sp3 = st.columns([1, 1, 1])
            with sp1:
                neuer_betrag = st.number_input(
                    "Betrag (€)",
                    min_value=0.0,
                    value=float(position["sparrate_betrag"]),
                    step=10.0,
                    key=f"betrag_{position['id']}"
                )
            with sp2:
                intervall_value = int(position["sparrate_intervall"]) if position["sparrate_intervall"] in INTERVALL_OPTIONEN else 4
                neues_intervall = st.selectbox(
                    "Intervall",
                    options=list(INTERVALL_OPTIONEN.keys()),
                    format_func=lambda x: INTERVALL_OPTIONEN[x],
                    index=list(INTERVALL_OPTIONEN.keys()).index(intervall_value),
                    key=f"intervall_{position['id']}"
                )
            with sp3:
                st.write("")
                st.write("")
                if st.button("Speichern", key=f"save_sp_{position['id']}", use_container_width=True):
                    aktualisiere_sparrate(position["id"], neuer_betrag, neues_intervall)
                    st.success("Gespeichert!")
                    st.rerun()
            
            st.divider()
            st.markdown("**🔁 Dividenden-Behandlung**")
            st.caption(
                "Wenn dein Broker automatisches Reinvestment nicht anbietet, kannst du es hier deaktivieren."
            )
            neuer_reinvest = st.checkbox(
                "Dividende automatisch reinvestieren",
                value=bool(position["reinvest_dividende"]),
                key=f"reinvest_{position['id']}"
            )
            if neuer_reinvest != bool(position["reinvest_dividende"]):
                aktualisiere_reinvest(position["id"], neuer_reinvest)
                st.rerun()