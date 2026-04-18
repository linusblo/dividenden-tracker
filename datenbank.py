"""
Datenspeicherung über st.session_state (pro Browser-Session).
Ersetzt die vorherige SQLite-Implementierung.
"""
import streamlit as st
import pandas as pd


def _ensure_state():
    """Stellt sicher, dass die Session-State-Struktur existiert."""
    if "positionen_liste" not in st.session_state:
        st.session_state.positionen_liste = []
    if "naechste_id" not in st.session_state:
        st.session_state.naechste_id = 1


def init_db():
    """Initialisiert die 'Datenbank' (hier: den Session-State)."""
    _ensure_state()


def lade_positionen():
    """Lädt alle Positionen als DataFrame."""
    _ensure_state()
    if not st.session_state.positionen_liste:
        # Leerer DataFrame mit allen Spalten
        return pd.DataFrame(columns=[
            "id", "ticker", "stueckzahl", 
            "sparrate_betrag", "sparrate_intervall", "reinvest_dividende"
        ])
    return pd.DataFrame(st.session_state.positionen_liste)


def speichere_position(ticker, stueckzahl):
    """Speichert eine neue Position oder aktualisiert eine vorhandene."""
    _ensure_state()
    ticker = ticker.upper()
    
    # Schon vorhanden? Dann aktualisieren.
    for pos in st.session_state.positionen_liste:
        if pos["ticker"] == ticker:
            pos["stueckzahl"] = stueckzahl
            return
    
    # Sonst neue Position anlegen
    st.session_state.positionen_liste.append({
        "id": st.session_state.naechste_id,
        "ticker": ticker,
        "stueckzahl": stueckzahl,
        "sparrate_betrag": 0.0,
        "sparrate_intervall": 4,
        "reinvest_dividende": 1,
    })
    st.session_state.naechste_id += 1


def aktualisiere_sparrate(position_id, betrag, intervall):
    """Aktualisiert die Sparrate einer Position."""
    _ensure_state()
    for pos in st.session_state.positionen_liste:
        if pos["id"] == position_id:
            pos["sparrate_betrag"] = betrag
            pos["sparrate_intervall"] = intervall
            return


def aktualisiere_reinvest(position_id, reinvest):
    """Aktualisiert den Reinvest-Modus einer Position."""
    _ensure_state()
    for pos in st.session_state.positionen_liste:
        if pos["id"] == position_id:
            pos["reinvest_dividende"] = 1 if reinvest else 0
            return


def loesche_position(position_id):
    """Löscht eine Position anhand ihrer ID."""
    _ensure_state()
    st.session_state.positionen_liste = [
        pos for pos in st.session_state.positionen_liste 
        if pos["id"] != position_id
    ]