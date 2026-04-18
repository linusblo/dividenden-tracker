"""
Marktdaten-Abruf über yfinance.
"""
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=3600)
def hole_aktien_daten(ticker):
    """Holt aktuelle Daten einer Aktie von yfinance."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        
        # Prüfe, ob wir überhaupt Daten bekommen haben
        if not info or len(info) < 5:
            return None
        
        kurs = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        if kurs == 0:
            # Fallback: Historie letzter Tag
            hist = t.history(period="5d")
            if not hist.empty:
                kurs = float(hist["Close"].iloc[-1])
        
        return {
            "name": info.get("shortName") or info.get("longName") or ticker,
            "kurs": kurs,
            "waehrung": info.get("currency", "USD"),
            "dividende_jahr": info.get("dividendRate", 0) or 0,
            "dividenden_rendite": info.get("dividendYield", 0) or 0,
        }
    except Exception as e:
        # Bei lokalem Debugging sichtbar
        print(f"Fehler beim Abruf von {ticker}: {e}")
        return None


@st.cache_data(ttl=3600)
def hole_dividenden_historie(ticker):
    """Holt die historischen Dividendenzahlungen."""
    try:
        t = yf.Ticker(ticker)
        dividenden = t.dividends
        if dividenden.empty:
            return None
        return dividenden
    except Exception:
        return None


@st.cache_data(ttl=3600)
def hole_wechselkurs(von_waehrung, nach_waehrung="EUR"):
    """Holt den aktuellen Wechselkurs."""
    if von_waehrung == nach_waehrung:
        return 1.0
    try:
        ticker_symbol = f"{von_waehrung}{nach_waehrung}=X"
        t = yf.Ticker(ticker_symbol)
        kurs = t.info.get("regularMarketPrice")
        if not kurs:
            hist = t.history(period="5d")
            if not hist.empty:
                kurs = float(hist["Close"].iloc[-1])
        return float(kurs) if kurs else None
    except Exception:
        return None


def in_euro(betrag, waehrung):
    """Rechnet einen Betrag in Euro um."""
    kurs = hole_wechselkurs(waehrung, "EUR")
    if kurs is None:
        return None
    return betrag * kurs


def von_euro(betrag, waehrung):
    """Rechnet Euro in eine andere Währung um."""
    if waehrung == "EUR":
        return betrag
    kurs = hole_wechselkurs(waehrung, "EUR")
    if kurs is None or kurs == 0:
        return None
    return betrag / kurs