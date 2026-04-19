"""
Datenbank-Zugriff über Supabase (PostgreSQL in der Cloud).
"""
import streamlit as st
import pandas as pd
from supabase import create_client, Client


@st.cache_resource
def _get_client() -> Client:
    """Erstellt den Supabase-Client (einmalig gecacht)."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def init_db():
    """
    Mit Supabase wird die Tabelle einmalig manuell im Dashboard angelegt.
    Diese Funktion prüft nur, ob die Verbindung funktioniert.
    """
    try:
        _get_client()
    except Exception as e:
        st.error(f"Fehler bei der Datenbank-Verbindung: {e}")


def lade_positionen():
    """Lädt alle Positionen aus der Datenbank."""
    try:
        client = _get_client()
        response = client.table("positionen").select("*").order("id").execute()
        data = response.data
        if not data:
            return pd.DataFrame(columns=[
                "id", "ticker", "stueckzahl",
                "sparrate_betrag", "sparrate_intervall", "reinvest_dividende"
            ])
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Fehler beim Laden der Positionen: {e}")
        return pd.DataFrame(columns=[
            "id", "ticker", "stueckzahl",
            "sparrate_betrag", "sparrate_intervall", "reinvest_dividende"
        ])


def speichere_position(ticker, stueckzahl):
    """Speichert eine neue Position oder aktualisiert eine vorhandene."""
    try:
        client = _get_client()
        ticker = ticker.upper()
        
        # Prüfen ob Position schon existiert
        existing = client.table("positionen").select("id").eq("ticker", ticker).execute()
        
        if existing.data:
            # Aktualisieren
            client.table("positionen").update({
                "stueckzahl": stueckzahl
            }).eq("ticker", ticker).execute()
        else:
            # Neu einfügen
            client.table("positionen").insert({
                "ticker": ticker,
                "stueckzahl": stueckzahl,
                "sparrate_betrag": 0,
                "sparrate_intervall": 4,
                "reinvest_dividende": 1,
            }).execute()
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")


def aktualisiere_sparrate(position_id, betrag, intervall):
    """Aktualisiert die Sparrate einer Position."""
    try:
        client = _get_client()
        client.table("positionen").update({
            "sparrate_betrag": betrag,
            "sparrate_intervall": intervall,
        }).eq("id", position_id).execute()
    except Exception as e:
        st.error(f"Fehler beim Aktualisieren der Sparrate: {e}")


def aktualisiere_reinvest(position_id, reinvest):
    """Aktualisiert den Reinvest-Modus einer Position."""
    try:
        client = _get_client()
        client.table("positionen").update({
            "reinvest_dividende": 1 if reinvest else 0,
        }).eq("id", position_id).execute()
    except Exception as e:
        st.error(f"Fehler beim Aktualisieren: {e}")


def loesche_position(position_id):
    """Löscht eine Position."""
    try:
        client = _get_client()
        client.table("positionen").delete().eq("id", position_id).execute()
    except Exception as e:
        st.error(f"Fehler beim Löschen: {e}")